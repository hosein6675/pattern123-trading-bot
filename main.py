import os
import logging
import hashlib

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Update

from modules.trading_engine import TradingEngine
from modules.config import active_config
from modules.telegram_bot import TelegramBot
from modules.dashboard import render
from modules.mt5_market_gateway import mt5_market_gateway
from modules.mt5_execution_gateway import mt5_execution_gateway


logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Pattern 123 Trading Assistant")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
TELEGRAM_TRANSPORT = os.getenv("TELEGRAM_TRANSPORT", "webhook").strip().lower()
TELEGRAM_WEBHOOK_PATH = "/telegram/webhook"
TELEGRAM_WEBHOOK_SECRET = hashlib.sha256(WEBHOOK_SECRET.encode("utf-8")).hexdigest() if WEBHOOK_SECRET else ""
trading_engine = TradingEngine()
telegram_bot = None


@app.on_event("startup")
async def startup_event():
    global telegram_bot
    logging.info("Pattern123 Trading Bot Started")
    if BOT_TOKEN:
        telegram_bot = TelegramBot(BOT_TOKEN, trading_engine)
        telegram_bot.build()
        await telegram_bot.application.initialize()
        await telegram_bot.application.start()

        if TELEGRAM_TRANSPORT == "polling":
            await telegram_bot.application.bot.delete_webhook(drop_pending_updates=False)
            if telegram_bot.application.updater is None:
                raise RuntimeError("Telegram updater is unavailable for polling transport")
            await telegram_bot.application.updater.start_polling(drop_pending_updates=False)
            bot_info = await telegram_bot.application.bot.get_me()
            logging.info(
                "Telegram polling runtime verified: bot_username=%s bot_id=%s",
                bot_info.username,
                bot_info.id,
            )
            logging.info("Telegram polling started")
        else:
            if not RENDER_EXTERNAL_URL:
                raise RuntimeError("RENDER_EXTERNAL_URL is required for Telegram webhook runtime")
            webhook_url = f"{RENDER_EXTERNAL_URL}{TELEGRAM_WEBHOOK_PATH}"
            await telegram_bot.application.bot.set_webhook(
                url=webhook_url,
                secret_token=TELEGRAM_WEBHOOK_SECRET,
                drop_pending_updates=False,
            )
            webhook_info = await telegram_bot.application.bot.get_webhook_info()
            bot_info = await telegram_bot.application.bot.get_me()
            logging.info(
                "Telegram runtime verified: bot_username=%s bot_id=%s webhook_url=%s pending=%s last_error=%s last_error_date=%s",
                bot_info.username,
                bot_info.id,
                webhook_info.url,
                webhook_info.pending_update_count,
                webhook_info.last_error_message,
                webhook_info.last_error_date,
            )
            logging.info("Telegram webhook registered")
    else:
        logging.warning("BOT_TOKEN not found. Telegram disabled.")


@app.on_event("shutdown")
async def shutdown_event():
    global telegram_bot
    if telegram_bot:
        if TELEGRAM_TRANSPORT == "polling" and telegram_bot.application.updater is not None:
            await telegram_bot.application.updater.stop()
        else:
            await telegram_bot.application.bot.delete_webhook(drop_pending_updates=False)
        await telegram_bot.application.stop()
        await telegram_bot.application.shutdown()
        logging.info("Telegram bot stopped")
    logging.info("Pattern123 Trading Bot Stopped")


@app.get("/")
async def health():
    return {
        "status": "online",
        "service": "pattern123-trading-bot",
        "mode": active_config.mode,
        "symbol": active_config.symbol,
        "telegram": "enabled" if telegram_bot else "disabled",
        "telegram_transport": TELEGRAM_TRANSPORT if telegram_bot else "disabled",
    }


@app.get("/health")
async def health_alias():
    return await health()


@app.post(TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Receive Telegram updates through Render's long-lived HTTP service."""
    if telegram_bot is None:
        return {"ok": False, "error": "telegram_disabled"}
    if TELEGRAM_TRANSPORT != "webhook":
        return {"ok": False, "error": "webhook_transport_disabled"}
    if not WEBHOOK_SECRET or request.headers.get("X-Telegram-Bot-Api-Secret-Token") != TELEGRAM_WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    try:
        payload = await request.json()
        update = Update.de_json(payload, telegram_bot.application.bot)
        if update is None:
            return {"ok": False, "error": "invalid_update"}
        await telegram_bot.application.process_update(update)
    except Exception:
        logging.exception("Telegram webhook processing failed")
        return {"ok": False, "error": "update_processing_failed"}
    return {"ok": True}


@app.get("/broker/status")
async def broker_status():
    return trading_engine.orders.status()


@app.post("/analyze")
async def analyze_market(request: Request):
    data = await request.json()
    symbol = data.get("symbol", active_config.symbol)
    timeframe = data.get("timeframe", active_config.timeframe)
    candles = data.get("candles", [])
    return {"ok": True, "analysis": trading_engine.analyze_market(symbol, timeframe, candles)}


@app.post("/webhook/market")
async def market_webhook(request: Request):
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    data = await request.json()
    symbol = data.get("symbol", active_config.symbol)
    timeframe = data.get("timeframe", active_config.timeframe)
    candles = data.get("candles", [])
    return {"ok": True, "result": trading_engine.analyze_market(symbol, timeframe, candles)}


@app.post("/webhook/mt5")
async def mt5_market_webhook(request: Request):
    if not WEBHOOK_SECRET:
        return {"ok": False, "error": "MT5 webhook secret is not configured"}
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "invalid_json"}
    accepted, reason = mt5_market_gateway.ingest(data)
    if not accepted:
        return {"ok": False, "error": reason}
    symbol = str(data.get("symbol", "")).upper()
    return {
        "ok": True,
        "source": "mt5",
        "demo_mode": False,
        "symbol": symbol,
        "live_tick_time": int(data["tick"]["time"]),
        "timeframes": list(data.get("timeframes", {}).keys()),
    }


@app.get("/webhook/mt5/status")
async def mt5_market_status(request: Request):
    if not WEBHOOK_SECRET:
        return {"ok": False, "error": "MT5 webhook secret is not configured"}
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    symbol = request.query_params.get("symbol", active_config.symbol)
    return {"ok": True, "market": mt5_market_gateway.status(symbol)}


@app.get("/webhook/mt5/commands")
async def mt5_execution_commands(request: Request):
    if not WEBHOOK_SECRET:
        return {"ok": False, "error": "MT5 webhook secret is not configured"}
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    symbol = request.query_params.get("symbol")
    commands = mt5_execution_gateway.pending(symbol)
    return {"ok": True, "command": commands[0] if commands else None, "commands": commands}


@app.post("/webhook/mt5/command-result")
async def mt5_execution_result(request: Request):
    if not WEBHOOK_SECRET:
        return {"ok": False, "error": "MT5 webhook secret is not configured"}
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "invalid_json"}
    accepted, reason = mt5_execution_gateway.accept_result(data)
    return {"ok": accepted, "result": reason}


@app.get("/execution/status")
async def execution_status(request: Request):
    if WEBHOOK_SECRET and request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    return {"ok": True, "execution": mt5_execution_gateway.status()}


@app.get("/dashboard/state")
async def dashboard_state():
    return trading_engine.dashboard_snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return render(trading_engine.dashboard_snapshot())


@app.post("/trade/test")
async def test_trade():
    if active_config.mode != "demo":
        return {"ok": False, "error": "Demo trade endpoint is disabled in live mode"}
    result = trading_engine.execute_order(
        symbol=active_config.symbol,
        direction="buy",
        volume=0.01,
        stop_loss=1.0,
        take_profit=1.2,
    )
    return {"ok": True, "order": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

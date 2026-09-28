import os
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

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
        await telegram_bot.application.updater.start_polling()
        logging.info("Telegram bot started")
    else:
        logging.warning("BOT_TOKEN not found. Telegram disabled.")


@app.on_event("shutdown")
async def shutdown_event():
    global telegram_bot
    if telegram_bot:
        await telegram_bot.application.updater.stop()
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
    }


@app.get("/health")
async def health_alias():
    return await health()


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

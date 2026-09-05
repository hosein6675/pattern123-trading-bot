import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from modules.config import active_config
from modules.dashboard import render
from modules.multi_timeframe_analysis import analyze as analyze_multi_timeframe
from modules.telegram_bot import TelegramBot
from modules.telegram_controls import TelegramSelection
from modules.trading_engine import TradingEngine

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Pattern 123 Trading Assistant")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
TEST_TRADE_ENABLED = os.getenv("TEST_TRADE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
trading_engine = TradingEngine()
telegram_bot = None


@app.on_event("startup")
async def startup_event():
    global telegram_bot
    logging.info("Pattern123 Trading Bot Started")
    if BOT_TOKEN:
        telegram_bot = TelegramBot(BOT_TOKEN, trading_engine); telegram_bot.build()
        await telegram_bot.application.initialize(); await telegram_bot.application.start(); await telegram_bot.application.updater.start_polling()
        logging.info("Telegram bot started")
    else: logging.warning("BOT_TOKEN not found. Telegram disabled.")


@app.on_event("shutdown")
async def shutdown_event():
    global telegram_bot
    if telegram_bot:
        await telegram_bot.application.updater.stop(); await telegram_bot.application.stop(); await telegram_bot.application.shutdown(); logging.info("Telegram bot stopped")
    logging.info("Pattern123 Trading Bot Stopped")


@app.get("/")
async def health(): return {"status": "online", "service": "pattern123-trading-bot", "mode": active_config.mode, "symbol": active_config.symbol}


@app.get("/broker/status")
async def broker_status(): return trading_engine.orders.status()


@app.post("/analyze")
async def analyze_market(request: Request):
    data = await request.json(); symbol = data.get("symbol", active_config.symbol); timeframe = data.get("timeframe", active_config.timeframe); candles = data.get("candles", [])
    return {"ok": True, "analysis": trading_engine.analyze_market(symbol, timeframe, candles)}


@app.post("/webhook/market")
async def market_webhook(request: Request):
    if not WEBHOOK_SECRET or request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET: return {"ok": False, "error": "unauthorized"}
    data = await request.json(); symbol = data.get("symbol", active_config.symbol); timeframe = data.get("timeframe", active_config.timeframe); candles = data.get("candles", [])
    return {"ok": True, "result": trading_engine.analyze_market(symbol, timeframe, candles)}


@app.post("/mt5/signal")
async def mt5_signal(request: Request):
    """Authenticated MTF signal API for the EA. It never executes trades."""
    if not WEBHOOK_SECRET or request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET: return {"ok": False, "error": "unauthorized"}
    data = await request.json(); symbol = str(data.get("symbol", active_config.symbol)).upper()
    selection = TelegramSelection(structure_timeframe=str(data.get("structure_timeframe", "H4")).upper(), analysis_timeframe=str(data.get("analysis_timeframe", "M15")).upper(), trigger_timeframe=str(data.get("trigger_timeframe", "M1")).upper(), symbols={symbol})
    candles = {str(k).upper(): v for k, v in (data.get("candles") or {}).items()}
    multi = analyze_multi_timeframe(trading_engine, symbol, selection, candles)
    trigger = multi.trigger
    decision = trigger.get("decision") if isinstance(trigger, dict) else getattr(trigger, "decision", "NO_TRADE")
    direction = getattr(decision, "direction", "none") if not isinstance(decision, str) else "none"
    if isinstance(decision, dict): direction = decision.get("direction", "none")
    strategy = trigger.get("strategy") if isinstance(trigger, dict) else getattr(trigger, "strategy", None)
    entry = float(getattr(strategy, "entry", 0.0) if strategy is not None else 0.0); stop = float(getattr(strategy, "stop_loss", 0.0) if strategy is not None else 0.0); target = float(getattr(strategy, "tp3", 0.0) if strategy is not None else 0.0); confidence = int(getattr(strategy, "confidence", 0) if strategy is not None else 0)
    approved = bool(getattr(strategy, "approved", False) if strategy is not None else False) and direction in {"buy", "sell"} and multi.status == "ready"
    return {"ok": True, "status": "signal" if approved else "NO_TRADE", "symbol": symbol, "direction": direction if approved else "none", "entry": entry, "stop_loss": stop, "take_profit": target, "confidence": confidence, "warnings": list(multi.warnings)}


@app.get("/dashboard/state")
async def dashboard_state(): return trading_engine.dashboard_snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(): return render(trading_engine.dashboard_snapshot())


@app.post("/trade/test")
async def test_trade():
    if not TEST_TRADE_ENABLED or active_config.mode != "demo": return {"ok": False, "error": "Test trade endpoint is disabled"}
    result = trading_engine.execute_order(symbol=active_config.symbol, direction="buy", volume=0.01, stop_loss=1.0, take_profit=1.2)
    return {"ok": True, "order": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000")); uvicorn.run("main:app", host="0.0.0.0", port=port)

import os
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from modules.trading_engine import TradingEngine
from modules.config import active_config
from modules.telegram_bot import TelegramBot
from modules.dashboard import render


logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Pattern 123 Trading Assistant")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
trading_engine = TradingEngine()
telegram_bot = None


@app.on_event("startup")
async def startup_event():
    global telegram_bot
    logging.info("Pattern123 Trading Bot Started")
    if BOT_TOKEN:
        telegram_bot = TelegramBot(BOT_TOKEN)
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
    return {"status": "online", "service": "pattern123-trading-bot", "mode": active_config.mode, "symbol": active_config.symbol}


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


@app.get("/dashboard/state")
async def dashboard_state():
    return trading_engine.dashboard_snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return render(trading_engine.dashboard_snapshot())


@app.post("/trade/test")
async def test_trade():
    result = trading_engine.execute_order(
        symbol=active_config.symbol,
        direction="buy",
        volume=0.01,
        stop_loss=0,
        take_profit=0,
    )
    return {"ok": True, "order": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from modules.config import active_config
from modules.dashboard import render
from modules.journal import JournalEngine
from modules.mt5_reporter import MT5Reporter
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
mt5_reporter = MT5Reporter(BOT_TOKEN)


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


def _authorized(request: Request) -> bool:
    return bool(WEBHOOK_SECRET) and request.headers.get("X-Webhook-Secret") == WEBHOOK_SECRET


@app.get("/")
async def health():
    return {"status": "online", "service": "pattern123-trading-bot", "mode": active_config.mode, "symbol": active_config.symbol}


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
    if not _authorized(request):
        return {"ok": False, "error": "unauthorized"}
    data = await request.json()
    symbol = data.get("symbol", active_config.symbol)
    timeframe = data.get("timeframe", active_config.timeframe)
    candles = data.get("candles", [])
    return {"ok": True, "result": trading_engine.analyze_market(symbol, timeframe, candles)}


@app.post("/mt5/signal")
async def mt5_signal(request: Request):
    if not _authorized(request):
        return {"ok": False, "error": "unauthorized"}
    data = await request.json()
    symbol = str(data.get("symbol", active_config.symbol)).upper()
    selection = TelegramSelection(
        structure_timeframe=str(data.get("structure_timeframe", "H4")).upper(),
        analysis_timeframe=str(data.get("analysis_timeframe", "M15")).upper(),
        trigger_timeframe=str(data.get("trigger_timeframe", "M1")).upper(),
        symbols={symbol},
    )
    candles = {str(k).upper(): v for k, v in (data.get("candles") or {}).items()}
    multi = analyze_multi_timeframe(trading_engine, symbol, selection, candles)
    trigger = multi.trigger
    decision = trigger.get("decision") if isinstance(trigger, dict) else getattr(trigger, "decision", "NO_TRADE")
    direction = getattr(decision, "direction", "none") if not isinstance(decision, str) else "none"
    if isinstance(decision, dict):
        direction = decision.get("direction", "none")
    strategy = trigger.get("strategy") if isinstance(trigger, dict) else getattr(trigger, "strategy", None)
    entry = float(getattr(strategy, "entry", 0.0) if strategy is not None else 0.0)
    stop = float(getattr(strategy, "stop_loss", 0.0) if strategy is not None else 0.0)
    target = float(getattr(strategy, "tp3", 0.0) if strategy is not None else 0.0)
    confidence = int(getattr(strategy, "confidence", 0) if strategy is not None else 0)
    approved = bool(getattr(strategy, "approved", False) if strategy is not None else False) and direction in {"buy", "sell"} and multi.status == "ready"
    return {"ok": True, "status": "signal" if approved else "NO_TRADE", "symbol": symbol, "direction": direction if approved else "none", "entry": entry, "stop_loss": stop, "take_profit": target, "confidence": confidence, "warnings": list(multi.warnings)}


@app.post("/mt5/report")
async def mt5_report(request: Request):
    if not _authorized(request):
        return {"ok": False, "error": "unauthorized"}
    data = await request.json()
    symbol = str(data.get("symbol", ""))
    balance = float(data.get("balance", 0))
    equity = float(data.get("equity", 0))
    positions = int(data.get("positions", 0))
    pnl = float(data.get("floating_pnl", 0))
    magic = str(data.get("magic", ""))
    text = f"💹 MT5 Statement\n\nSymbol: {symbol}\nBalance: {balance:.2f}\nEquity: {equity:.2f}\nOpen positions: {positions}\nFloating P/L: {pnl:.2f}\nMagic: {magic}"
    sent = await mt5_reporter.send(text)
    return {"ok": True, "sent": sent}


@app.post("/mt5/trade-event")
async def mt5_trade_event(request: Request):
    if not _authorized(request):
        return {"ok": False, "error": "unauthorized"}
    data = await request.json()
    event = str(data.get("event", "")).upper()
    symbol = str(data.get("symbol", "")).upper()
    if event not in {"OPEN", "CLOSE", "MODIFY"} or not symbol:
        return {"ok": False, "error": "invalid_trade_event"}

    journal = trading_engine.journal
    order_id = data.get("order_id")
    deal_id = data.get("deal_id")
    position_id = data.get("position_id")
    existing = journal.find_by_broker_deal(deal_id) if deal_id else None
    if existing is None and position_id:
        existing = journal.find_by_broker_position(position_id)
    if existing is None and order_id:
        existing = journal.find_by_broker_order(order_id)

    if event == "OPEN":
        if existing is not None:
            journal.update_trade(existing.trade_id, broker_order_id=str(order_id) if order_id else existing.broker_order_id, broker_deal_id=str(deal_id) if deal_id else existing.broker_deal_id, broker_position_id=str(position_id) if position_id else existing.broker_position_id)
            return {"ok": True, "action": "linked", "journal_id": existing.trade_id}
        record = journal.create_trade(
            symbol=symbol,
            timeframe=str(data.get("timeframe", "M15")).upper(),
            direction=str(data.get("direction", "none")).lower(),
            entry_price=float(data.get("price", 0)),
            stop_loss=float(data.get("stop_loss", 0)),
            take_profit=float(data.get("take_profit", 0)),
            result="OPEN",
            profit_loss=0.0,
            reason="MT5 Demo execution",
            analysis=str(data.get("analysis", "")),
            entry_time=str(data.get("time", "")) or None,
            broker_order_id=order_id,
            broker_deal_id=deal_id,
            broker_position_id=position_id,
            risk_percent=float(data.get("risk_percent", 0)),
            reward_risk=float(data.get("reward_risk", 0)),
            market_context=str(data.get("market_context", "")),
        )
        return {"ok": True, "action": "created", "journal_id": record.trade_id}

    if existing is None:
        return {"ok": False, "error": "journal_record_not_found"}

    if event == "MODIFY":
        updated = journal.update_trade(existing.trade_id, stop_loss=float(data.get("stop_loss", existing.stop_loss)), take_profit=float(data.get("take_profit", existing.take_profit)), broker_order_id=str(order_id) if order_id else existing.broker_order_id, broker_deal_id=str(deal_id) if deal_id else existing.broker_deal_id, broker_position_id=str(position_id) if position_id else existing.broker_position_id)
        return {"ok": True, "action": "modified", "journal_id": updated.trade_id if updated else None}

    exit_price = float(data.get("price", existing.exit_price or existing.entry_price))
    pnl = float(data.get("profit", 0))
    updated = journal.update_trade(existing.trade_id, exit_price=exit_price, exit_time=str(data.get("time", "")) or journal._now(), result="CLOSED", profit_loss=pnl, broker_deal_id=str(deal_id) if deal_id else existing.broker_deal_id, broker_position_id=str(position_id) if position_id else existing.broker_position_id)
    return {"ok": True, "action": "closed", "journal_id": updated.trade_id if updated else None, "profit_loss": pnl}


@app.get("/dashboard/state")
async def dashboard_state():
    return trading_engine.dashboard_snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return render(trading_engine.dashboard_snapshot())


@app.post("/trade/test")
async def test_trade():
    if not TEST_TRADE_ENABLED or active_config.mode != "demo":
        return {"ok": False, "error": "Test trade endpoint is disabled"}
    result = trading_engine.execute_order(symbol=active_config.symbol, direction="buy", volume=0.01, stop_loss=1.0, take_profit=1.2)
    return {"ok": True, "order": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

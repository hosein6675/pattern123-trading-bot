import os
import asyncio
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")

app = FastAPI(title="Pattern 123 Trading Assistant")
telegram_app = None

TIMEFRAMES = {
    "1H": "1h",
    "4H": "4h",
    "D": "1d",
    "W": "1w",
}

def macd(close, fast, slow, signal):
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()
    line = fast_ema - slow_ema
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist

def analyze_ohlc(rows: list[dict[str, Any]], symbol: str, timeframe: str) -> dict[str, Any]:
    """Core, mechanical MVP based only on rules explicitly supplied in this chat.
    It is intentionally conservative: no trade is emitted without enough structure."""
    df = pd.DataFrame(rows)
    if df.empty or len(df) < 80:
        return {"ok": False, "reason": "حداقل ۸۰ کندل برای تحلیل لازم است."}

    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().reset_index(drop=True)

    # Moving averages requested by the user.
    for n in [30, 60, 100, 200]:
        df[f"ma{n}"] = df["close"].ewm(span=n, adjust=False).mean()

    # Three requested MACDs.
    df["macd_default"], df["macd_default_sig"], df["macd_default_hist"] = macd(df.close, 12, 26, 9)
    df["macd_quarter"], df["macd_quarter_sig"], df["macd_quarter_hist"] = macd(df.close, 3, 6, 2)
    df["macd_4x"], df["macd_4x_sig"], df["macd_4x_hist"] = macd(df.close, 48, 104, 36)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Broad trend state from price vs MA stack + 4x MACD.
    bullish = (
        last.ma30 > last.ma60 > last.ma100 > last.ma200
        and last.macd_4x > last.macd_4x_sig
    )
    bearish = (
        last.ma30 < last.ma60 < last.ma100 < last.ma200
        and last.macd_4x < last.macd_4x_sig
    )

    # Simple swing points (fractal-style confirmation; non-repainting on completed bars).
    highs = []
    lows = []
    for i in range(2, len(df)-2):
        if df.high[i] > df.high[i-1] and df.high[i] > df.high[i-2] and df.high[i] >= df.high[i+1] and df.high[i] >= df.high[i+2]:
            highs.append((i, float(df.high[i])))
        if df.low[i] < df.low[i-1] and df.low[i] < df.low[i-2] and df.low[i] <= df.low[i+1] and df.low[i] <= df.low[i+2]:
            lows.append((i, float(df.low[i])))

    if not highs or not lows:
        return {"ok": True, "symbol": symbol, "timeframe": timeframe, "state": "نامشخص",
                "message": "ساختار فرکتالی کافی پیدا نشد؛ سیگنال صادر نشد."}

    last_high_i, last_high = highs[-1]
    last_low_i, last_low = lows[-1]

    # Fibonacci depth of the latest completed swing.
    if last_low_i < last_high_i:
        swing_low, swing_high = last_low, last_high
        direction = "صعودی"
    else:
        swing_low, swing_high = last_low, last_high
        direction = "نزولی"

    rng = abs(swing_high - swing_low)
    fib = {
        "38.2": swing_high - 0.382 * rng,
        "50": swing_high - 0.50 * rng,
        "61.8": swing_high - 0.618 * rng,
        "78.6": swing_high - 0.786 * rng,
    }

    # Conservative confidence: descriptive only, not a guarantee/probability.
    score = 0
    if bullish or bearish:
        score += 30
    if (bullish and last.macd_default > last.macd_default_sig) or (bearish and last.macd_default < last.macd_default_sig):
        score += 25
    if (bullish and last.macd_quarter > last.macd_quarter_sig) or (bearish and last.macd_quarter < last.macd_quarter_sig):
        score += 25
    if (bullish and last.close > last.ma60) or (bearish and last.close < last.ma60):
        score += 20

    state = "صعودی" if bullish else "نزولی" if bearish else "خنثی/انتقالی"

    return {
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "state": state,
        "confidence": score,
        "price": float(last.close),
        "swing_high": swing_high,
        "swing_low": swing_low,
        "fib": fib,
        "macd": {
            "default": float(last.macd_default),
            "quarter": float(last.macd_quarter),
            "4x": float(last.macd_4x),
        },
        "message": "این خروجی تحلیل اولیه است. تا وقتی شرایط کامل Pattern 123 و تأییدهای ورود تکمیل نشده، ربات نباید معامله‌ای را پیشنهاد کند."
    }

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 ساختار", callback_data="structure")],
        [InlineKeyboardButton("📈 MACDها", callback_data="macd"),
         InlineKeyboardButton("〽️ Moving Average", callback_data="ma")],
        [InlineKeyboardButton("🧩 Price Action", callback_data="pa"),
         InlineKeyboardButton("🧩 Price Action Fractal", callback_data="paf")],
        [InlineKeyboardButton("🔔 هشدارها", callback_data="alerts")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 دستیار Pattern 123\n\n"
        "ماژول‌های فعلی بر اساس قوانین مشخص‌شده در گفتگو ساخته شده‌اند.\n"
        "برای تحلیل، ابتدا نماد و تایم‌فریم را مشخص کنید.",
        reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    texts = {
        "structure": "📊 ساختار\nتایم‌فریم‌های ماژور: 1H / 4H / D\nدرگاه دریافت OHLC برای تحلیل ساختار آماده است.",
        "macd": "📈 MACD\nDefault: 12,26,9\nQuarter: 3,6,2\n4x: 48,104,36",
        "ma": "〽️ Moving Average\nEMA 30 / 60 / 100 / 200",
        "pa": "📐 Price Action\nتشخیص سوئینگ‌ها، اصلاح و سطوح در حال پیاده‌سازی.",
        "paf": "🧩 Price Action Fractal\nفرکتال‌های تأییدشده روی کندل‌های بسته بررسی می‌شوند.",
        "alerts": "🔔 هشدارها\nزیرساخت دریافت هشدار وبهوک آماده است.",
        "settings": "⚙️ تنظیمات\nدر نسخه بعدی نماد، تایم‌فریم و سطح هشدار قابل تنظیم می‌شود.",
    }
    await q.edit_message_text(texts[q.data], reply_markup=menu())

@app.post("/webhook/market")
async def market_webhook(request: Request):
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {"ok": False, "error": "unauthorized"}
    payload = await request.json()
    result = analyze_ohlc(payload.get("rows", []), payload.get("symbol", "UNKNOWN"), payload.get("timeframe", "UNKNOWN"))
    return result

@app.get("/")
async def health():
    return {"status": "online", "service": "pattern123-trading-bot"}

async def run_bot():
    global telegram_app
    if not BOT_TOKEN:
        return
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

if __name__ == "__main__":
    import uvicorn
    # Render can run the web server; Telegram polling runs in the same process.
    asyncio.run(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))

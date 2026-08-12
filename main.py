import os
import asyncio
import logging
from typing import Any

import pandas as pd
import uvicorn
from fastapi import FastAPI, Request

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")

app = FastAPI(title="Pattern 123 Trading Assistant")

telegram_app = None



def menu():def settings_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 انتخاب بازار", callback_data="market"),
        ],
        [
            InlineKeyboardButton("🪙 انتخاب نماد", callback_data="symbol"),
        ],
        [
            InlineKeyboardButton("⏱ تایم‌فریم", callback_data="timeframe"),
        ],
        [
            InlineKeyboardButton("📰 اخبارها", callback_data="news"),
        ],
        [
            InlineKeyboardButton("⬅️ بازگشت", callback_data="back"),
        ],
    ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 ساختار", callback_data="structure")],
        [
            InlineKeyboardButton("📈 MACD", callback_data="macd"),
            InlineKeyboardButton("〽️ MA", callback_data="ma")
        ],
        [
            InlineKeyboardButton("🧩 Price Action", callback_data="pa"),
            InlineKeyboardButton("🔔 هشدارها", callback_data="alerts")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 دستیار Pattern 123 فعال شد.\n\n"
        "سیستم آماده دریافت درخواست است.",
        reply_markup=menu()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "structure": "📊 ماژول ساختار فعال است.",
        "macd": "📈 MACD: Default / Quarter / 4x",
        "ma": "〽️ Moving Average: EMA 30/60/100/200",
        "pa": "🧩 Price Action آماده توسعه است.",
        "alerts": "🔔 سیستم هشدار آماده است.",
        "settings": "⚙️ تنظیمات در نسخه بعدی تکمیل می‌شود.",
    }

    await query.edit_message_text(
        messages.get(query.data, "OK"),
        reply_markup=menu()
    )

async def start_telegram():
    global telegram_app

    if not BOT_TOKEN:
        logging.warning("BOT_TOKEN not found. Telegram disabled.")
        return

    telegram_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CallbackQueryHandler(button)
    )

    await telegram_app.initialize()
    await telegram_app.start()

    await telegram_app.updater.start_polling()

    logging.info("Telegram bot started")


async def stop_telegram():
    global telegram_app

    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_telegram())
    logging.info("FastAPI started")


@app.on_event("shutdown")
async def shutdown_event():
    await stop_telegram()


@app.get("/")
async def health():
    return {
        "status": "online",
        "service": "pattern123-trading-bot"
    }


@app.post("/webhook/market")
async def market_webhook(request: Request):
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        return {
            "ok": False,
            "error": "unauthorized"
        }

    data = await request.json()

    return {
        "ok": True,
        "received": data
    }


def analyze_ohlc(
    rows: list[dict[str, Any]],
    symbol: str,
    timeframe: str
):
    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "ok": False,
            "reason": "No data"
        }

    return {
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "message": "Analysis module ready"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )

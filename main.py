import os
import asyncio
import logging

import uvicorn
from fastapi import FastAPI, Request

from modules.trading_engine import TradingEngine
from modules.config import active_config


logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title="Pattern 123 Trading Assistant"
)


WEBHOOK_SECRET = os.getenv(
    "WEBHOOK_SECRET",
    "change-me"
)


trading_engine = TradingEngine()



@app.on_event("startup")
async def startup_event():

    logging.info(
        "Pattern123 Trading Bot Started"
    )



@app.on_event("shutdown")
async def shutdown_event():

    logging.info(
        "Pattern123 Trading Bot Stopped"
    )



@app.get("/")
async def health():

    return {

        "status": "online",

        "service": "pattern123-trading-bot",

        "mode": active_config.mode,

        "symbol": active_config.symbol

    }



@app.post("/webhook/market")
async def market_webhook(request: Request):


    if request.headers.get(
        "X-Webhook-Secret"
    ) != WEBHOOK_SECRET:

        return {

            "ok": False,

            "error": "unauthorized"

        }



    data = await request.json()



    symbol = data.get(
        "symbol",
        active_config.symbol
    )


    timeframe = data.get(
        "timeframe",
        active_config.timeframe
    )


    candles = data.get(
        "candles",
        []
    )



    result = trading_engine.analyze_market(

        symbol,

        timeframe,

        candles

    )



    return {

        "ok": True,

        "result": result

    }




@app.post("/trade/test")
async def test_trade():

    result = trading_engine.execute_order(

        symbol=active_config.symbol,

        direction="buy",

        volume=0.01,

        stop_loss=0,

        take_profit=0

    )


    return {

        "ok": True,

        "order": result

    }





if __name__ == "__main__":


    port = int(

        os.getenv(

            "PORT",

            "10000"

        )

    )


    uvicorn.run(

        "main:app",

        host="0.0.0.0",

        port=port

    )

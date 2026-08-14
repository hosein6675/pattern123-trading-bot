from dataclasses import dataclass
from datetime import datetime, timedelta

import MetaTrader5 as mt5
import pandas as pd


@dataclass
class Candle:

    symbol: str
    timeframe: str
    timestamp: str

    open: float
    high: float
    low: float
    close: float

    volume: float = 0



TIMEFRAME_MAP = {

    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,

    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,

    "D1": mt5.TIMEFRAME_D1

}



class MarketDataEngine:


    def __init__(self):

        if not mt5.initialize():

            raise Exception(
                "MT5 connection failed"
            )

        self.provider = "mt5"



    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        days: int = 100
    ):


        if timeframe not in TIMEFRAME_MAP:

            raise ValueError(
                "Unsupported timeframe"
            )


        end = datetime.now()

        start = end - timedelta(
            days=days
        )


        rates = mt5.copy_rates_range(

            symbol,

            TIMEFRAME_MAP[timeframe],

            start,

            end

        )


        if rates is None:

            return {

                "symbol": symbol,
                "timeframe": timeframe,
                "candles": [],
                "count": 0,
                "provider": self.provider,
                "status": "no_data",
                "created_at": str(datetime.utcnow())

            }


        df = pd.DataFrame(
            rates
        )


        candles = []


        for _, row in df.iterrows():

            candles.append({

                "symbol": symbol,

                "timeframe": timeframe,

                "timestamp":
                    str(
                        datetime.fromtimestamp(
                            row["time"]
                        )
                    ),

                "open":
                    float(row["open"]),

                "high":
                    float(row["high"]),

                "low":
                    float(row["low"]),

                "close":
                    float(row["close"]),

                "volume":
                    float(row["tick_volume"])

            })



        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "candles": candles,

            "count": len(candles),

            "provider": self.provider,

            "status": "ready",

            "created_at": str(datetime.utcnow())

        }



    def add_candle(
        self,
        candle: Candle
    ):

        return candle



    def shutdown(self):

        mt5.shutdown()

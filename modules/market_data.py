from dataclasses import dataclass
from datetime import datetime


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



class MarketDataEngine:


    def __init__(self):

        self.provider = "demo"



    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ):

        candles = []


        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "candles": candles,

            "count": len(candles),

            "provider": self.provider,

            "status": "ready",

            "created_at": str(datetime.utcnow())

        }



    def add_candle(self, candle: Candle):

        return candle

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
    volume: float


class MarketDataEngine:

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ):

        # در نسخه دمو به دیتا پروایدر واقعی وصل می‌شود
        # فعلاً فقط ساختار آماده است

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": limit,
            "status": "data provider ready",
            "created_at": str(datetime.utcnow())
        }

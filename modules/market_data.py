from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


class MarketDataEngine:
    VALID_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
    DEFAULT_CANDLE_COUNT = 200
    DEMO_PRICES = {"EURUSD": 1.1, "GBPUSD": 1.3, "USDJPY": 150.0, "XAUUSD": 2400.0, "BTCUSD": 60000.0, "ETHUSD": 3000.0}
    TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}

    def __init__(self) -> None:
        self.demo_mode = True

    def get_candles(self, symbol: str, timeframe: str, days: int = 200) -> dict:
        if not symbol:
            return {"status": "error", "candles": [], "message": "Symbol is required"}
        symbol, timeframe = str(symbol).upper(), str(timeframe).upper()
        if timeframe not in self.VALID_TIMEFRAMES:
            return {"status": "error", "candles": [], "message": "Unsupported timeframe"}
        try:
            count = max(int(days), self.DEFAULT_CANDLE_COUNT)
        except (TypeError, ValueError):
            count = self.DEFAULT_CANDLE_COUNT
        return {"status": "ready", "symbol": symbol, "timeframe": timeframe, "candles": self._generate_demo_candles(symbol, timeframe, count), "source": "demo", "demo_mode": True}

    def _generate_demo_candles(self, symbol: str, timeframe: str, count: int = 200) -> list[dict]:
        count = max(int(count), self.DEFAULT_CANDLE_COUNT)
        base = self._base_price(symbol)
        step = self.TIMEFRAME_MINUTES[timeframe]
        start = datetime.now(timezone.utc) - timedelta(minutes=step * count)
        candles, previous = [], base
        for i in range(count):
            wave = math.sin(i / 9.0) * 0.0015 + math.sin(i / 17.0) * 0.0007
            close = base * (1.0 + wave + (i / max(count - 1, 1)) * 0.002)
            volatility = base * (0.0008 + abs(math.sin(i / 5.0)) * 0.0005)
            candles.append({"time": (start + timedelta(minutes=step * i)).isoformat(), "open": round(previous, 5), "high": round(max(previous, close) + volatility, 5), "low": round(min(previous, close) - volatility, 5), "close": round(close, 5), "volume": 1000 + i % 500})
            previous = close
        return candles

    def _base_price(self, symbol: str) -> float:
        return self.DEMO_PRICES.get(str(symbol).upper(), 100.0)

    def get_current_price(self, symbol: str) -> dict:
        if not symbol:
            return {"status": "error", "symbol": "", "price": None, "source": "demo", "message": "Symbol is required"}
        symbol = str(symbol).upper()
        return {"status": "ready", "symbol": symbol, "price": round(self._base_price(symbol), 5), "source": "demo", "demo_mode": True}

    def is_available(self) -> bool:
        return True

    def get_status(self) -> dict:
        return {"status": "ready", "source": "demo", "demo_mode": True, "provider": "internal_demo"}

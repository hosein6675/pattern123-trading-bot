from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


class MarketDataEngine:
    VALID_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
    DEFAULT_CANDLE_COUNT = 200
    DEMO_PRICES = {
        "EURUSD": 1.10000,
        "GBPUSD": 1.30000,
        "USDJPY": 150.00000,
        "XAUUSD": 2400.00000,
        "BTCUSD": 60000.00000,
        "ETHUSD": 3000.00000,
    }
    TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}

    def __init__(self) -> None:
        self.demo_mode = True

    def get_candles(self, symbol: str, timeframe: str, days: int = 200) -> dict:
        if not symbol:
            return {"status": "error", "candles": [], "message": "Symbol is required"}
        symbol = str(symbol).upper()
        timeframe = str(timeframe).upper()
        if timeframe not in self.VALID_TIMEFRAMES:
            return {"status": "error", "candles": [], "message": "Unsupported timeframe"}
        try:
            count = max(int(days), self.DEFAULT_CANDLE_COUNT)
        except (TypeError, ValueError):
            count = self.DEFAULT_CANDLE_COUNT
        try:
            candles = self._generate_demo_candles(symbol, timeframe, count)
        except Exception as exc:
            return {"status": "error", "candles": [], "message": f"Failed to generate market data: {exc}"}
        return {"status": "ready", "symbol": symbol, "timeframe": timeframe, "candles": candles, "source": "demo", "demo_mode": True, "message": "Demo market data"}

    def _generate_demo_candles(self, symbol: str, timeframe: str, count: int = 200) -> list[dict]:
        count = max(int(count), self.DEFAULT_CANDLE_COUNT)
        base_price = self._base_price(symbol)
        step_minutes = self.TIMEFRAME_MINUTES[timeframe]
        start_time = datetime.now(timezone.utc) - timedelta(minutes=step_minutes * count)
        candles = []
        previous_close = base_price
        for i in range(count):
            wave = math.sin(i / 9.0) * 0.0015 + math.sin(i / 17.0) * 0.0007
            trend = (i / max(count - 1, 1)) * 0.002
            close_price = base_price * (1.0 + wave + trend)
            open_price = previous_close
            volatility = base_price * (0.0008 + abs(math.sin(i / 5.0)) * 0.0005)
            timestamp = start_time + timedelta(minutes=step_minutes * i)
            candles.append({
                "time": timestamp.isoformat(),
                "open": round(open_price, 5),
                "high": round(max(open_price, close_price) + volatility, 5),
                "low": round(min(open_price, close_price) - volatility, 5),
                "close": round(close_price, 5),
                "volume": 1000 + (i % 500),
            })
            previous_close = close_price
        return candles

    def _base_price(self, symbol: str) -> float:
        return self.DEMO_PRICES.get(str(symbol).upper(), 100.0)

    def get_current_price(self, symbol: str) -> dict:
        if not symbol:
            return {"status": "error", "symbol": "", "price": None, "source": "demo", "message": "Symbol is required"}
        symbol = str(symbol).upper()
        return {"status": "ready", "symbol": symbol, "price": round(self._base_price(symbol), 5), "source": "demo", "demo_mode": True, "message": "Demo current price"}

    def is_available(self) -> bool:
        return True

    def get_status(self) -> dict:
        return {"status": "ready", "source": "demo", "demo_mode": True, "provider": "internal_demo"}

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from modules.config import active_config


class MarketDataEngine:
    VALID_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
    DEFAULT_CANDLE_COUNT = 200
    DEMO_PRICES = {
        "EURUSD": 1.1,
        "GBPUSD": 1.3,
        "USDJPY": 150.0,
        "XAUUSD": 2400.0,
        "BTCUSD": 60000.0,
        "ETHUSD": 3000.0,
    }
    TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}

    def __init__(self) -> None:
        self.demo_mode = active_config.mode != "live"
        self.broker = None
        if not self.demo_mode:
            from modules.broker_interface import BrokerInterface
            self.broker = BrokerInterface()

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

        if not self.demo_mode and self.broker is not None:
            result = self.broker.broker.get_candles(symbol, timeframe, count)
            if result.get("status") != "ready":
                return result
            return result

        return {
            "status": "ready",
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": self._generate_demo_candles(symbol, timeframe, count),
            "source": "demo",
            "demo_mode": True,
        }

    def _generate_demo_candles(self, symbol, timeframe, count=200):
        count = max(int(count), self.DEFAULT_CANDLE_COUNT)
        base = self._base_price(symbol)
        step = self.TIMEFRAME_MINUTES[timeframe]
        start = datetime.now(timezone.utc) - timedelta(minutes=step * count)
        candles = []
        previous = base
        for i in range(count):
            wave = math.sin(i / 9.0) * 0.0015 + math.sin(i / 17.0) * 0.0007
            close = base * (1.0 + wave + (i / max(count - 1, 1)) * 0.002)
            volatility = base * (0.0008 + abs(math.sin(i / 5.0)) * 0.0005)
            candles.append({
                "time": (start + timedelta(minutes=step * i)).isoformat(),
                "open": round(previous, 5),
                "high": round(max(previous, close) + volatility, 5),
                "low": round(min(previous, close) - volatility, 5),
                "close": round(close, 5),
                "volume": 1000 + i % 500,
            })
            previous = close
        return candles

    def _base_price(self, symbol):
        return self.DEMO_PRICES.get(str(symbol).upper(), 100.0)

    def get_current_price(self, symbol):
        if not symbol:
            return {"status": "error", "symbol": "", "price": None, "message": "Symbol is required"}
        symbol = str(symbol).upper()
        if not self.demo_mode and self.broker is not None:
            tick = self.broker.current_price(symbol)
            if tick.get("status") != "ready":
                return tick
            return {"status": "ready", "symbol": symbol, "price": (tick["bid"] + tick["ask"]) / 2.0, "source": "mt5", "demo_mode": False}
        return {"status": "ready", "symbol": symbol, "price": round(self._base_price(symbol), 5), "source": "demo", "demo_mode": True}

    def is_available(self):
        return self.demo_mode or self.broker is not None

    def get_status(self):
        if not self.demo_mode and self.broker is not None:
            status = self.broker.status()
            return {"status": status.get("status", "error"), "source": "mt5", "demo_mode": False, "provider": "MetaTrader5", "message": status.get("message", "")}
        return {"status": "ready", "source": "demo", "demo_mode": True, "provider": "internal_demo"}

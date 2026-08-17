title: market_data.py

from datetime import datetime, timedelta
import math

class MarketDataEngine:

```
VALID_TIMEFRAMES = (
    "M1",
    "M5",
    "M15",
    "H1",
    "H4",
    "D1",
)

DEFAULT_CANDLE_COUNT = 200

DEMO_PRICES = {
    "EURUSD": 1.10000,
    "GBPUSD": 1.30000,
    "USDJPY": 150.00000,
    "XAUUSD": 2400.00000,
    "BTCUSD": 60000.00000,
    "ETHUSD": 3000.00000,
}

TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

def __init__(self):
    self.demo_mode = True

def get_candles(self, symbol, timeframe, days=200):
    if not symbol:
        return {
            "status": "error",
            "candles": [],
            "message": "Symbol is required",
        }

    symbol = str(symbol).upper()
    timeframe = str(timeframe).upper()

    if timeframe not in self.VALID_TIMEFRAMES:
        return {
            "status": "error",
            "candles": [],
            "message": "Unsupported timeframe",
        }

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = self.DEFAULT_CANDLE_COUNT

    if days <= 0:
        days = self.DEFAULT_CANDLE_COUNT

    count = max(self.DEFAULT_CANDLE_COUNT, days)

    try:
        candles = self._generate_demo_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )
    except Exception as exc:
        return {
            "status": "error",
            "candles": [],
            "message": f"Failed to generate market data: {exc}",
        }

    return {
        "status": "ready",
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "source": "demo",
        "demo_mode": True,
        "message": "Demo market data",
    }

def _generate_demo_candles(self, symbol, timeframe, count=200):
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = self.DEFAULT_CANDLE_COUNT

    count = max(count, self.DEFAULT_CANDLE_COUNT)

    base_price = self._base_price(symbol)
    step_minutes = self.TIMEFRAME_MINUTES[timeframe]

    start_time = (
        datetime.utcnow()
        - timedelta(minutes=step_minutes * count)
    )

    candles = []
    previous_close = base_price

    for i in range(count):
        wave_primary = math.sin(i / 9.0)
        wave_secondary = math.sin(i / 17.0)

        trend_factor = i / max(count - 1, 1)

        wave = (
            wave_primary * 0.0015
            + wave_secondary * 0.0007
        )

        trend = trend_factor * 0.002

        close_price = (
            base_price
            * (1.0 + wave + trend)
        )

        open_price = previous_close

        volatility_factor = (
            0.0008
            + abs(math.sin(i / 5.0)) * 0.0005
        )

        volatility = base_price * volatility_factor

        high_price = (
            max(open_price, close_price)
            + volatility
        )

        low_price = (
            min(open_price, close_price)
            - volatility
        )

        timestamp = (
            start_time
            + timedelta(minutes=step_minutes * i)
        )

        candle = {
            "time": timestamp.isoformat(),
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
            "volume": 1000 + (i % 500),
        }

        candles.append(candle)
        previous_close = close_price

    return candles

def _base_price(self, symbol):
    symbol = str(symbol).upper()

    return self.DEMO_PRICES.get(
        symbol,
        100.00000,
    )

def get_current_price(self, symbol):
    if not symbol:
        return {
            "status": "error",
            "symbol": "",
            "price": None,
            "source": "demo",
            "message": "Symbol is required",
        }

    symbol = str(symbol).upper()
    price = self._base_price(symbol)

    return {
        "status": "ready",
        "symbol": symbol,
        "price": round(price, 5),
        "source": "demo",
        "demo_mode": True,
        "message": "Demo current price",
    }

def is_available(self):
    return True

def get_status(self):
    return {
        "status": "ready",
        "source": "demo",
        "demo_mode": True,
        "provider": "internal_demo",
    }
```

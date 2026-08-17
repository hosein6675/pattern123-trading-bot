def __init__(self):
    self.demo_mode = True

def get_candles(self, symbol, timeframe, days=200):
    if not symbol:
        return {
            "status": "error",
            "candles": [],
            "message": "Symbol is required",
        }

    valid_timeframes = (
        "M1",
        "M5",
        "M15",
        "H1",
        "H4",
        "D1",
    )

    if timeframe not in valid_timeframes:
        return {
            "status": "error",
            "candles": [],
            "message": "Unsupported timeframe",
        }

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 200

    if days <= 0:
        days = 200

    candles = self._generate_demo_candles(
        symbol,
        timeframe,
        max(200, days),
    )

    return {
        "status": "ready",
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "source": "demo",
        "demo_mode": True,
        "message": "Demo market data",
    }

def _generate_demo_candles(
    self,
    symbol,
    timeframe,
    count=200,
):
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 200

    count = max(count, 200)

    base_price = self._base_price(symbol)

    timeframe_minutes = {
        "M1": 1,
        "M5": 5,
        "M15": 15,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
    }

    step_minutes = timeframe_minutes.get(
        timeframe,
        60,
    )

    start_time = datetime.utcnow() - timedelta(
        minutes=step_minutes * count
    )

    candles = []
    previous_close = base_price

    for i in range(count):
        wave = math.sin(i / 9.0)
        wave *= base_price * 0.0015

        trend = (i / count)
        trend *= base_price * 0.002

        close_price = base_price + wave + trend
        open_price = previous_close

        volatility = base_price * 0.0008
        volatility += (
            abs(math.sin(i / 5.0))
            * base_price
            * 0.0005
        )

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

    demo_prices = {
        "EURUSD": 1.10000,
        "GBPUSD": 1.30000,
        "USDJPY": 150.00000,
        "XAUUSD": 2400.00000,
        "BTCUSD": 60000.00000,
        "ETHUSD": 3000.00000,
    }

    return demo_prices.get(
        symbol,
        100.00000,
    )

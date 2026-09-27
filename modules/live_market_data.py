from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}


def _finite_positive(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def validate_tick(tick: dict[str, Any], now: datetime | None = None, max_age_seconds: int = 120) -> tuple[bool, str]:
    if tick.get("source") != "mt5" or tick.get("demo_mode") is not False:
        return False, "Market tick provenance is not MT5"
    if not _finite_positive(tick.get("bid")) or not _finite_positive(tick.get("ask")):
        return False, "Invalid MT5 bid/ask"
    if float(tick["ask"]) < float(tick["bid"]):
        return False, "Invalid MT5 spread"
    try:
        timestamp = int(tick["time"])
    except (TypeError, ValueError):
        return False, "Invalid MT5 tick timestamp"
    current = now or datetime.now(timezone.utc)
    age = current.timestamp() - timestamp
    if age < -5:
        return False, "MT5 tick timestamp is in the future"
    if age > max_age_seconds:
        return False, f"MT5 tick is stale ({int(age)}s)"
    return True, ""


def validate_candles(
    market: dict[str, Any],
    timeframe: str,
    now: datetime | None = None,
    minimum_count: int = 50,
) -> tuple[bool, str]:
    timeframe = str(timeframe).upper()
    if market.get("source") != "mt5" or market.get("demo_mode") is not False:
        return False, "Market candles provenance is not MT5"
    candles = market.get("candles")
    if not isinstance(candles, list) or len(candles) < minimum_count:
        return False, "Insufficient MT5 candles"
    if timeframe not in TIMEFRAME_MINUTES:
        return False, "Unsupported timeframe"

    previous_time = None
    for candle in candles:
        try:
            timestamp = int(candle["time"])
            opening = float(candle["open"])
            high = float(candle["high"])
            low = float(candle["low"])
            close = float(candle["close"])
        except (KeyError, TypeError, ValueError):
            return False, "Malformed MT5 candle"
        if timestamp <= 0:
            return False, "Invalid MT5 candle timestamp"
        if previous_time is not None and timestamp <= previous_time:
            return False, "MT5 candle timestamps are not strictly increasing"
        previous_time = timestamp
        if not all(math.isfinite(value) and value > 0 for value in (opening, high, low, close)):
            return False, "Invalid MT5 OHLC values"
        if high < max(opening, close) or low > min(opening, close) or high < low:
            return False, "Invalid MT5 OHLC relationship"

    current = now or datetime.now(timezone.utc)
    age = current.timestamp() - previous_time
    allowed_age = max(120, TIMEFRAME_MINUTES[timeframe] * 60 * 2.5)
    if age < -5:
        return False, "Latest MT5 candle timestamp is in the future"
    if age > allowed_age:
        return False, f"MT5 {timeframe} candles are stale ({int(age)}s)"
    return True, ""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

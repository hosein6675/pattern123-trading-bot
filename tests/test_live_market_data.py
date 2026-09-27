from datetime import datetime, timezone

from modules.live_market_data import validate_candles, validate_tick


def _fresh_timestamp():
    return int(datetime.now(timezone.utc).timestamp())


def _candles(count=50, timestamp=None):
    timestamp = timestamp or _fresh_timestamp()
    return [
        {
            "time": timestamp - (count - i) * 60,
            "open": 1.1000,
            "high": 1.1010,
            "low": 1.0990,
            "close": 1.1005,
            "volume": 100,
        }
        for i in range(count)
    ]


def test_tick_requires_mt5_provenance():
    ok, reason = validate_tick(
        {"source": "demo", "demo_mode": True, "bid": 1.1, "ask": 1.2, "time": _fresh_timestamp()}
    )
    assert not ok
    assert "MT5" in reason


def test_tick_rejects_stale_data():
    ok, reason = validate_tick(
        {"source": "mt5", "demo_mode": False, "bid": 1.1, "ask": 1.2, "time": _fresh_timestamp() - 121}
    )
    assert not ok
    assert "stale" in reason


def test_candles_require_mt5_provenance():
    market = {"source": "demo", "demo_mode": True, "candles": _candles()}
    ok, reason = validate_candles(market, "M1")
    assert not ok
    assert "MT5" in reason


def test_candles_accept_fresh_valid_mt5_data():
    market = {"source": "mt5", "demo_mode": False, "candles": _candles()}
    ok, reason = validate_candles(market, "M1")
    assert ok, reason


def test_candles_reject_bad_ohlc():
    candles = _candles()
    candles[-1]["low"] = 2.0
    market = {"source": "mt5", "demo_mode": False, "candles": candles}
    ok, reason = validate_candles(market, "M1")
    assert not ok
    assert "OHLC" in reason

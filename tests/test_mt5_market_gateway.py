from datetime import datetime, timezone

from modules.mt5_market_gateway import MT5MarketGateway


def candles(count=50):
    base = int(datetime.now(timezone.utc).timestamp()) - 60
    return [
        {
            "time": base - (count - 1 - i) * 60,
            "open": 100.0 + i,
            "high": 101.0 + i,
            "low": 99.0 + i,
            "close": 100.5 + i,
            "volume": 1000,
        }
        for i in range(count)
    ]


def payload():
    now = int(datetime.now(timezone.utc).timestamp())
    return {
        "source": "mt5",
        "demo_mode": False,
        "symbol": "EURUSD",
        "tick": {"bid": 100.0, "ask": 100.1, "time": now},
        "timeframes": {tf: candles() for tf in ("M1", "M5", "M15", "H1", "H4", "D1")},
    }


def test_gateway_accepts_complete_live_mt5_snapshot():
    gateway = MT5MarketGateway()
    ok, reason = gateway.ingest(payload())
    assert ok, reason
    market = gateway.get_candles("EURUSD", "M15")
    assert market["status"] == "ready"
    assert market["source"] == "mt5"
    assert market["demo_mode"] is False
    assert len(market["candles"]) == 50


def test_gateway_rejects_non_mt5_provenance():
    gateway = MT5MarketGateway()
    data = payload()
    data["source"] = "demo"
    ok, reason = gateway.ingest(data)
    assert not ok
    assert "provenance" in reason.lower()


def test_gateway_rejects_missing_timeframe():
    gateway = MT5MarketGateway()
    data = payload()
    del data["timeframes"]["H4"]
    ok, reason = gateway.ingest(data)
    assert not ok
    assert reason.startswith("H4:")


def test_gateway_fails_closed_when_no_snapshot_exists():
    gateway = MT5MarketGateway()
    market = gateway.get_candles("EURUSD", "M1")
    assert market["status"] == "error"
    assert market["source"] == "mt5"
    assert market["demo_mode"] is False


def test_gateway_status_is_unavailable_before_live_snapshot():
    gateway = MT5MarketGateway()
    status = gateway.status("EURUSD")
    assert status["status"] == "unavailable"
    assert status["source"] == "mt5"
    assert status["demo_mode"] is False


def test_gateway_accepts_additional_real_mt5_timeframe():
    gateway = MT5MarketGateway()
    data = payload()
    extra = candles()
    data["timeframes"]["S1"] = [
        {**item, "time": int(item["time"]) * 1} for item in extra
    ]
    ok, reason = gateway.ingest(data)
    assert ok, reason
    market = gateway.get_candles("EURUSD", "S1")
    assert market["status"] == "ready"
    assert market["source"] == "mt5"


def test_gateway_rejects_unrequested_timeframe_lookup():
    gateway = MT5MarketGateway()
    ok, reason = gateway.ingest(payload())
    assert ok, reason
    market = gateway.get_candles("EURUSD", "S1")
    assert market["status"] == "error"
    assert "not been received" in market["message"]

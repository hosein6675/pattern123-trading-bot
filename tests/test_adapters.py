from datetime import datetime, timezone

from modules.market_intelligence.backtest.adapters import ReplayAdapter


def test_adapter_preserves_provider_payload_and_orders_by_timestamp():
    first = {"ts": datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc), "value": "a"}
    second = {"ts": datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc), "value": "b"}

    events = list(ReplayAdapter("test", [second, first]).events(lambda row: row["ts"]))

    assert [event.payload["value"] for event in events] == ["a", "b"]
    assert all(event.timestamp.tzinfo is not None for event in events)

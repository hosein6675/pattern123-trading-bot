from datetime import datetime, timezone

import pytest

from modules.market_intelligence.order_flow.models import OrderFlowSnapshot


def base(**overrides):
    values = {
        "provider": "cme",
        "instrument": "ES",
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "bid": 100.0,
        "ask": 100.25,
        "bid_size": 1.0,
        "ask_size": 1.0,
        "delta": 0.0,
        "cumulative_delta": 0.0,
        "volume": 2.0,
    }
    values.update(overrides)
    return OrderFlowSnapshot(**values)


def test_valid_order_flow_snapshot():
    base().validate()


@pytest.mark.parametrize("field", ["delta", "cumulative_delta", "volume"])
def test_non_finite_numeric_values_are_rejected(field):
    with pytest.raises(ValueError, match="finite"):
        base(**{field: float("nan")}).validate()


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        base(timestamp=datetime(2026, 1, 1)).validate()

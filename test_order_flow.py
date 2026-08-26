from datetime import datetime, timezone

import pytest

from modules.market_intelligence.order_flow import OrderFlowSnapshot
from modules.market_intelligence.order_flow.service import OrderFlowService


def snapshot() -> OrderFlowSnapshot:
    return OrderFlowSnapshot(
        provider="test",
        instrument="XAUUSD",
        timestamp=datetime.now(timezone.utc),
        bid=100.0,
        ask=100.1,
        bid_size=10,
        ask_size=12,
        delta=-2,
        volume=22,
    )


def test_snapshot_validation_accepts_valid_data() -> None:
    snapshot().validate()


def test_snapshot_validation_rejects_invalid_book() -> None:
    bad = snapshot()
    object.__setattr__(bad, "bid", 101.0)
    with pytest.raises(ValueError, match="bid cannot exceed ask"):
        bad.validate()


def test_empty_service_is_disabled() -> None:
    service = OrderFlowService()
    assert service.enabled is False
    assert service.snapshots("XAUUSD") == ()

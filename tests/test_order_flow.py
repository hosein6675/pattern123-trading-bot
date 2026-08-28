from datetime import datetime, timezone

import pytest

from modules.market_intelligence.order_flow.models import OrderFlowSnapshot
from modules.market_intelligence.order_flow.provider import DisabledOrderFlowProvider
from modules.market_intelligence.order_flow.service import OrderFlowService


class StubProvider:
    def __init__(self, snapshots):
        self._snapshots = snapshots

    def fetch(self, instrument, since=None):
        return self._snapshots


def snapshot():
    return OrderFlowSnapshot(
        provider="stub",
        instrument="ES",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        bid=100,
        ask=101,
        bid_size=5,
        ask_size=4,
        delta=1,
        cumulative_delta=10,
        volume=9,
    )


def test_disabled_provider_is_safe_default():
    service = OrderFlowService([DisabledOrderFlowProvider()])
    assert service.enabled is False
    assert service.snapshots("ES") == ()


def test_enabled_service_collects_and_validates():
    item = snapshot()
    service = OrderFlowService([StubProvider([item])], enabled=True)
    assert service.snapshots("ES") == (item,)


def test_empty_instrument_is_rejected():
    service = OrderFlowService()
    with pytest.raises(ValueError, match="instrument"):
        service.snapshots("  ")


def test_invalid_bid_ask_is_rejected():
    item = snapshot()
    invalid = OrderFlowSnapshot(
        provider=item.provider,
        instrument=item.instrument,
        timestamp=item.timestamp,
        bid=102,
        ask=101,
    )
    service = OrderFlowService([StubProvider([invalid])], enabled=True)
    with pytest.raises(ValueError, match="bid"):
        service.snapshots("ES")

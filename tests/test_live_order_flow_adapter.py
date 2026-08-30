from datetime import datetime, timezone

import pytest

from modules.market_intelligence.order_flow.live_adapter import LiveOrderFlowAdapter, validate_snapshot
from modules.market_intelligence.order_flow.models import OrderFlowSnapshot


class Provider:
    def snapshots(self):
        return iter(())


def test_live_level2_is_disabled_by_default():
    assert tuple(LiveOrderFlowAdapter(Provider()).stream()) == ()


def test_live_level2_can_be_explicitly_enabled():
    adapter = LiveOrderFlowAdapter(Provider(), enabled=True)
    assert tuple(adapter.stream()) == ()


def test_snapshot_requires_timezone_aware_timestamp():
    snapshot = OrderFlowSnapshot("cme", "ES", datetime(2026, 1, 1), 1, 2, 1, 1, 0, 2)
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_snapshot(snapshot)

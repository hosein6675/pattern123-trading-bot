from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot


UTC = timezone.utc


def test_snapshot_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        BacktestSnapshot(datetime(2026, 1, 1), 100.0, {})


def test_snapshot_rejects_non_positive_price():
    with pytest.raises(ValueError, match="positive"):
        BacktestSnapshot(datetime(2026, 1, 1, tzinfo=UTC), 0.0, {})


def test_future_snapshot_is_rejected():
    timestamp = datetime(2026, 1, 1, 12, tzinfo=UTC)
    snapshot = BacktestSnapshot(timestamp, 100.0, {"pattern": "123"})
    with pytest.raises(ValueError, match="future"):
        snapshot.with_context_until(timestamp - timedelta(seconds=1))


def test_context_sources_remain_independent():
    snapshot = BacktestSnapshot(
        datetime(2026, 1, 1, tzinfo=UTC),
        100.0,
        {"pattern": "123"},
        news_data=("news",),
        order_flow_data=("delta",),
    )
    assert snapshot.pattern_data == {"pattern": "123"}
    assert snapshot.news_data == ("news",)
    assert snapshot.order_flow_data == ("delta",)

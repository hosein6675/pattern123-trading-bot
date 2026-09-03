from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot
from backtest.walk_forward import build_windows


UTC = timezone.utc


def make_snapshots(count: int):
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return [BacktestSnapshot(base + timedelta(minutes=i), 100 + i, {}) for i in range(count)]


def test_windows_are_strictly_chronological_and_non_overlapping():
    windows = build_windows(make_snapshots(6), train_size=3, test_size=1)
    assert len(windows) == 3
    assert windows[0].train[-1].timestamp < windows[0].test[0].timestamp
    assert windows[0].test[-1].timestamp < windows[1].test[0].timestamp


def test_insufficient_data_returns_no_window():
    assert build_windows(make_snapshots(3), 2, 2) == ()


def test_invalid_sizes_are_rejected():
    with pytest.raises(ValueError, match="positive"):
        build_windows(make_snapshots(4), 0, 2)


def test_out_of_order_data_is_rejected():
    items = make_snapshots(4)
    items[2], items[3] = items[3], items[2]
    with pytest.raises(ValueError, match="ordered"):
        build_windows(items, 2, 1)

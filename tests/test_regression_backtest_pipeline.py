from datetime import datetime, timedelta, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.mode import BacktestMode
from backtest.runner import BacktestRunner
from backtest.walk_forward import build_windows


def _data():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(BacktestSnapshot(base + timedelta(minutes=i), 100 + i, {}, (), ()) for i in range(10))


def test_regression_all_modes_keep_the_same_snapshot_boundary():
    snapshots = _data()
    for mode in BacktestMode:
        result = BacktestRunner(lambda _: 1.0, mode).run(snapshots)
        assert result.snapshots_processed == len(snapshots)
        assert len(result.decisions) == len(snapshots)


def test_walk_forward_windows_never_overlap_train_and_test():
    snapshots = _data()
    windows = build_windows(snapshots, train_size=4, test_size=2)
    for window in windows:
        train_times = {s.timestamp for s in window.train}
        test_times = {s.timestamp for s in window.test}
        assert train_times.isdisjoint(test_times)
        assert max(train_times) < min(test_times)

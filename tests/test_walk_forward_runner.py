from datetime import datetime, timedelta, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.mode import BacktestMode
from backtest.walk_forward_runner import run_walk_forward


def _snapshots(n=8):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [BacktestSnapshot(base + timedelta(minutes=i), 100 + i, {}, (), ()) for i in range(n)]


def test_walk_forward_runs_only_test_windows():
    seen = []

    def strategy(snapshot):
        seen.append(snapshot.timestamp)
        return 1.0

    results = run_walk_forward(_snapshots(), strategy, train_size=4, test_size=2)
    assert len(results) == 2
    assert len(seen) == 4
    assert seen == [r.timestamp for result in results for r in result.window.test]
    assert all(result.win_rate == 1.0 for result in results)


def test_walk_forward_isolated_mode_is_preserved():
    results = run_walk_forward(_snapshots(), lambda _: -1.0, 4, 2, BacktestMode.NEWS_ONLY)
    assert all(result.test_result.snapshots_processed == 2 for result in results)
    assert all(result.win_rate == 0.0 for result in results)

from datetime import datetime, timedelta, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.mode import BacktestMode
from backtest.runner import BacktestResult
from backtest.walk_forward import WalkForwardWindow
from backtest.walk_forward_runner import WalkForwardResult
from backtest.walk_forward_aggregate import aggregate


def _result(values):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    test = tuple(BacktestSnapshot(base + timedelta(minutes=i), 100 + i, {}, (), ()) for i in range(len(values)))
    window = WalkForwardWindow((), test)
    return WalkForwardResult(window, BacktestResult(tuple(values), len(values)), 0.0, 0.0, 0.0)


def test_aggregate_uses_only_test_decisions():
    report = aggregate((_result((1.0, -1.0)), _result((2.0, 3.0))))
    assert report.windows == 2
    assert report.test_snapshots == 4
    assert report.numeric_decisions == 4
    assert report.win_rate == 0.75
    assert report.profit_factor == 5.0


def test_aggregate_ignores_non_numeric_decisions():
    report = aggregate((_result(("bullish", 1.0)),))
    assert report.numeric_decisions == 1
    assert report.win_rate == 1.0

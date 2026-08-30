from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot
from backtest.runner import BacktestRunner


UTC = timezone.utc


def snapshot(minutes: int) -> BacktestSnapshot:
    return BacktestSnapshot(
        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes),
        100.0 + minutes,
        {"pattern": "123"},
        news_data=("news",),
        order_flow_data=("delta",),
    )


def test_runner_passes_isolated_snapshot_to_strategy():
    seen = []
    runner = BacktestRunner(lambda item: seen.append(item) or item.price)
    result = runner.run([snapshot(0), snapshot(1)])
    assert result.decisions == (100.0, 101.0)
    assert seen[0].news_data == ()
    assert seen[0].order_flow_data == ()
    assert seen[0].pattern_data == {"pattern": "123"}


def test_runner_rejects_out_of_order_snapshots():
    runner = BacktestRunner(lambda item: item.price)
    with pytest.raises(ValueError, match="ordered"):
        runner.run([snapshot(2), snapshot(1)])


def test_runner_enforces_as_of_boundary():
    runner = BacktestRunner(lambda item: item.price)
    with pytest.raises(ValueError, match="future"):
        runner.run([snapshot(1)], as_of=snapshot(0).timestamp)


def test_empty_run_is_valid():
    result = BacktestRunner(lambda item: item.price).run([])
    assert result.decisions == ()
    assert result.snapshots_processed == 0

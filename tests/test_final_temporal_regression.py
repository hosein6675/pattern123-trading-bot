from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot
from backtest.runner import BacktestRunner
from backtest.walk_forward import build_windows


def make_snapshot(minutes: int) -> BacktestSnapshot:
    return BacktestSnapshot(
        datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        100.0 + minutes,
        {"price": 100.0 + minutes},
        news_data=("n",),
        order_flow_data=("l2",),
    )


def test_future_observation_is_rejected():
    with pytest.raises(ValueError, match="future"):
        BacktestRunner(lambda snapshot: snapshot.price).run(
            [make_snapshot(2)], as_of=make_snapshot(1).timestamp
        )


def test_walk_forward_has_strict_train_test_boundary():
    windows = build_windows(tuple(make_snapshot(i) for i in range(8)), 4, 2)
    assert windows
    for window in windows:
        assert window.train[-1].timestamp < window.test[0].timestamp
        assert set(window.train).isdisjoint(window.test)

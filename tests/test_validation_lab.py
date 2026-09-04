from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot
from backtest.validation_lab import (
    TradeObservation,
    ValidationThresholds,
    apply_execution_costs,
    evaluate_gate,
    run_validation_lab,
    summarize,
    validate_walk_forward,
)
from modules.market_intelligence.backtest.execution import ExecutionCosts, ExecutionModel
from backtest.mode import BacktestMode


UTC = timezone.utc


def _snapshots(count=8):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        BacktestSnapshot(start + timedelta(days=i), 100 + i, {"i": i})
        for i in range(count)
    )


def test_summarize_tracks_profit_factor_expectancy_and_drawdown():
    summary = summarize(
        [
            TradeObservation(10),
            TradeObservation(-5),
            TradeObservation(8),
            TradeObservation(-20),
        ],
        starting_equity=100,
    )
    assert summary.trades == 4
    assert summary.win_rate == pytest.approx(0.5)
    assert summary.net_pnl == pytest.approx(-7)
    assert summary.profit_factor == pytest.approx(18 / 25)
    assert summary.expectancy == pytest.approx(-1.75)
    assert summary.max_drawdown == pytest.approx(20)
    assert summary.max_drawdown_pct == pytest.approx(20 / 113)


def test_execution_costs_are_explicit_and_deterministic():
    observations = apply_execution_costs(
        [TradeObservation(10)],
        ExecutionModel(),
        ExecutionCosts(spread=1, slippage=2, commission=0.5),
    )
    assert observations[0].pnl == pytest.approx(6.5)


def test_walk_forward_windows_are_strictly_chronological():
    windows = validate_walk_forward(_snapshots(), train_size=3, test_size=2)
    assert len(windows) == 2
    assert windows[0].train[-1].timestamp < windows[0].test[0].timestamp
    assert windows[1].train[-1].timestamp < windows[1].test[0].timestamp


def test_walk_forward_rejects_bad_source_order():
    snapshots = _snapshots()
    bad = (snapshots[1], snapshots[0], *snapshots[2:])
    with pytest.raises(ValueError, match="ordered"):
        validate_walk_forward(bad, train_size=2, test_size=2)


def test_gate_fails_when_oos_evidence_is_insufficient():
    gate = evaluate_gate(
        summarize([TradeObservation(2)]),
        summarize([TradeObservation(1)]),
        ValidationThresholds(minimum_oos_trades=2),
    )
    assert not gate.passed
    assert "Insufficient out-of-sample trades" in gate.reasons


def test_validation_lab_fits_a_fresh_strategy_per_window_and_keeps_oos_separate():
    created = []

    class Strategy:
        def __init__(self, mode):
            self.mode = mode
            self.fit_count = 0
            created.append(self)

        def fit(self, train):
            self.fit_count += 1
            assert train

        def __call__(self, snapshot):
            return snapshot.price - 100

    def factory(mode):
        return Strategy(mode)

    def extract(result, snapshot):
        return TradeObservation(float(result), timestamp=snapshot.timestamp)

    result = run_validation_lab(
        _snapshots(7),
        factory,
        extract,
        [BacktestMode.PATTERN_ONLY],
        train_size=3,
        test_size=2,
        thresholds=ValidationThresholds(minimum_oos_trades=1),
    )
    validation = result.modes[0]
    assert validation.windows == 2
    assert validation.gate.passed
    assert len(created) == 2
    assert all(strategy.fit_count == 1 for strategy in created)
    assert validation.out_of_sample.trades == 4

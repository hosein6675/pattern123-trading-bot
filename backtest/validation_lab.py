"""Research-grade validation utilities for deterministic strategy comparison.

The lab never creates market observations, signals, or execution assumptions.
All observations and execution costs are explicit inputs supplied by the caller.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from math import inf, isfinite, sqrt
from typing import Any

from modules.market_intelligence.backtest.execution import ExecutionCosts, ExecutionModel

from .data_snapshot import BacktestSnapshot
from .mode import BacktestMode
from .quality_gate import validate_snapshots
from .walk_forward import WalkForwardWindow, build_windows


@dataclass(frozen=True, slots=True)
class TradeObservation:
    """One realized strategy outcome supplied by the caller."""

    pnl: float
    direction: str = "none"
    approved: bool = True
    timestamp: Any | None = None


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    observations: int
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    expectancy: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_like: float
    average_win: float
    average_loss: float


@dataclass(frozen=True, slots=True)
class ValidationThresholds:
    """Explicit research acceptance thresholds; no threshold is hidden."""

    minimum_oos_trades: int = 30
    minimum_oos_profit_factor: float = 1.0
    minimum_oos_expectancy: float = 0.0
    maximum_oos_drawdown_pct: float = 0.20
    minimum_oos_to_is_expectancy_ratio: float = 0.0


@dataclass(frozen=True, slots=True)
class ValidationGate:
    passed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModeValidation:
    mode: str
    in_sample: PerformanceSummary
    out_of_sample: PerformanceSummary
    windows: int
    gate: ValidationGate


@dataclass(frozen=True, slots=True)
class ValidationLabResult:
    modes: tuple[ModeValidation, ...]
    execution_costs: ExecutionCosts


def _finite(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if isfinite(number) else default


def apply_execution_costs(
    observations: Iterable[TradeObservation],
    execution_model: ExecutionModel,
    costs: ExecutionCosts | None = None,
) -> tuple[TradeObservation, ...]:
    """Apply only explicitly supplied execution costs to gross P&L."""
    return tuple(
        TradeObservation(
            pnl=execution_model.net_pnl(observation.pnl, costs),
            direction=observation.direction,
            approved=observation.approved,
            timestamp=observation.timestamp,
        )
        for observation in observations
    )


def summarize(
    observations: Iterable[TradeObservation], starting_equity: float = 0.0
) -> PerformanceSummary:
    values = tuple(_finite(item.pnl) for item in observations if item.approved)
    wins = tuple(value for value in values if value > 0)
    losses = tuple(value for value in values if value < 0)
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    net_pnl = sum(values)

    equity = _finite(starting_equity)
    peak = equity
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    dd_pct = max_dd / peak if peak > 0 else 0.0
    mean = net_pnl / len(values) if values else 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values) if values else 0.0
    std = sqrt(variance)
    sharpe_like = mean / std if std > 0 else (inf if mean > 0 else 0.0)

    return PerformanceSummary(
        observations=len(values),
        trades=len(values),
        wins=len(wins),
        losses=len(losses),
        win_rate=len(wins) / len(values) if values else 0.0,
        net_pnl=net_pnl,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=(gross_profit / gross_loss) if gross_loss else (inf if gross_profit else 0.0),
        expectancy=mean,
        max_drawdown=max_dd,
        max_drawdown_pct=dd_pct,
        sharpe_like=sharpe_like,
        average_win=gross_profit / len(wins) if wins else 0.0,
        average_loss=sum(losses) / len(losses) if losses else 0.0,
    )


def validate_walk_forward(
    snapshots: Sequence[BacktestSnapshot],
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> tuple[WalkForwardWindow, ...]:
    """Validate source data and return strictly chronological windows."""
    return build_windows(validate_snapshots(snapshots), train_size, test_size, step)


def evaluate_gate(
    in_sample: PerformanceSummary,
    out_of_sample: PerformanceSummary,
    thresholds: ValidationThresholds = ValidationThresholds(),
) -> ValidationGate:
    reasons: list[str] = []
    if out_of_sample.trades < thresholds.minimum_oos_trades:
        reasons.append("Insufficient out-of-sample trades")
    if out_of_sample.profit_factor < thresholds.minimum_oos_profit_factor:
        reasons.append("Out-of-sample profit factor below threshold")
    if out_of_sample.expectancy <= thresholds.minimum_oos_expectancy:
        reasons.append("Out-of-sample expectancy is not positive")
    if out_of_sample.max_drawdown_pct > thresholds.maximum_oos_drawdown_pct:
        reasons.append("Out-of-sample drawdown exceeds threshold")

    if in_sample.expectancy > 0:
        ratio = out_of_sample.expectancy / in_sample.expectancy
        if ratio < thresholds.minimum_oos_to_is_expectancy_ratio:
            reasons.append("Out-of-sample expectancy degradation exceeds threshold")

    return ValidationGate(not reasons, tuple(reasons))


def _fit_if_supported(strategy: object, train: Sequence[BacktestSnapshot]) -> None:
    fit = getattr(strategy, "fit", None)
    if callable(fit):
        fit(tuple(train))


def run_validation_lab(
    snapshots: Sequence[BacktestSnapshot],
    strategy_factory: Callable[[BacktestMode], Callable[[BacktestSnapshot], object]],
    outcome_extractor: Callable[[object, BacktestSnapshot], TradeObservation | None],
    modes: Sequence[BacktestMode],
    train_size: int,
    test_size: int,
    step: int | None = None,
    execution_model: ExecutionModel | None = None,
    costs: ExecutionCosts | None = None,
    thresholds: ValidationThresholds = ValidationThresholds(),
) -> ValidationLabResult:
    """Run leakage-resistant walk-forward validation for explicit strategy variants.

    A fresh strategy instance is created for every walk-forward window. If that
    strategy exposes ``fit(train_snapshots)``, fitting occurs only on that
    window's training segment before the test segment is evaluated.
    """
    windows = validate_walk_forward(snapshots, train_size, test_size, step)
    model = execution_model or ExecutionModel()
    applied_costs = costs if costs is not None else model.default_costs
    results: list[ModeValidation] = []

    for mode in modes:
        train_obs: list[TradeObservation] = []
        test_obs: list[TradeObservation] = []
        for window in windows:
            strategy = strategy_factory(mode)
            _fit_if_supported(strategy, window.train)
            for snapshot in window.train:
                outcome = outcome_extractor(strategy(snapshot), snapshot)
                if outcome is not None:
                    train_obs.append(outcome)
            for snapshot in window.test:
                outcome = outcome_extractor(strategy(snapshot), snapshot)
                if outcome is not None:
                    test_obs.append(outcome)

        in_sample = summarize(apply_execution_costs(train_obs, model, applied_costs))
        out_of_sample = summarize(apply_execution_costs(test_obs, model, applied_costs))
        results.append(
            ModeValidation(
                mode=mode.value,
                in_sample=in_sample,
                out_of_sample=out_of_sample,
                windows=len(windows),
                gate=evaluate_gate(in_sample, out_of_sample, thresholds),
            )
        )

    return ValidationLabResult(tuple(results), applied_costs)

"""Research-grade validation utilities for deterministic strategy comparison.

The lab deliberately does not create market data, signals, or execution costs.
All observations must be supplied by the caller, and walk-forward test periods
are evaluated strictly after their corresponding training periods.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from math import inf, isfinite, sqrt

from .data_snapshot import BacktestSnapshot
from .execution_model import ExecutionCosts, ExecutionModel
from .mode import BacktestMode
from .quality_gate import validate_snapshots
from .walk_forward import WalkForwardWindow, build_windows


@dataclass(frozen=True, slots=True)
class TradeObservation:
    """One realized strategy outcome supplied by the caller."""

    pnl: float
    direction: str = "none"
    approved: bool = True
    timestamp: object | None = None


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
class ModeValidation:
    mode: str
    in_sample: PerformanceSummary
    out_of_sample: PerformanceSummary
    windows: int


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
    """Apply explicit costs to realized gross P&L without inventing inputs."""
    return tuple(
        TradeObservation(
            pnl=execution_model.net_pnl(observation.pnl, costs),
            direction=observation.direction,
            approved=observation.approved,
            timestamp=observation.timestamp,
        )
        for observation in observations
    )


def summarize(observations: Iterable[TradeObservation], starting_equity: float = 0.0) -> PerformanceSummary:
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
    denominator = peak if peak > 0 else 0.0
    dd_pct = (max_dd / denominator) if denominator else 0.0
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
    """Validate source data and return strictly chronological train/test windows."""
    checked = validate_snapshots(snapshots)
    return build_windows(checked, train_size, test_size, step)


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
) -> ValidationLabResult:
    """Compare strategies using only out-of-sample walk-forward observations.

    ``strategy_factory`` controls the strategy variant for each mode. The lab
    does not assume that a mode itself means Pattern/MACD/Trendline; callers
    explicitly map variants to modes, preventing accidental strategy coupling.
    """
    windows = validate_walk_forward(snapshots, train_size, test_size, step)
    model = execution_model or ExecutionModel()
    applied_costs = costs or model.default_costs
    results: list[ModeValidation] = []
    for mode in modes:
        strategy = strategy_factory(mode)
        train_obs: list[TradeObservation] = []
        test_obs: list[TradeObservation] = []
        for window in windows:
            for snapshot in window.train:
                outcome = outcome_extractor(strategy(snapshot), snapshot)
                if outcome is not None:
                    train_obs.append(outcome)
            for snapshot in window.test:
                outcome = outcome_extractor(strategy(snapshot), snapshot)
                if outcome is not None:
                    test_obs.append(outcome)
        train_costed = apply_execution_costs(train_obs, model, applied_costs)
        test_costed = apply_execution_costs(test_obs, model, applied_costs)
        results.append(
            ModeValidation(
                mode=mode.value,
                in_sample=summarize(train_costed),
                out_of_sample=summarize(test_costed),
                windows=len(windows),
            )
        )
    return ValidationLabResult(tuple(results), applied_costs)

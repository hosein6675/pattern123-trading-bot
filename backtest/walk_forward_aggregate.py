"""Aggregate walk-forward test metrics without mixing train observations."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import max_drawdown, profit_factor, win_rate
from .walk_forward_runner import WalkForwardResult


@dataclass(frozen=True, slots=True)
class WalkForwardAggregate:
    windows: int
    test_snapshots: int
    numeric_decisions: int
    win_rate: float
    profit_factor: float
    max_drawdown: float


def aggregate(results: tuple[WalkForwardResult, ...]) -> WalkForwardAggregate:
    decisions = tuple(
        value
        for result in results
        for value in result.test_result.decisions
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    )
    return WalkForwardAggregate(
        windows=len(results),
        test_snapshots=sum(r.test_result.snapshots_processed for r in results),
        numeric_decisions=len(decisions),
        win_rate=win_rate(decisions),
        profit_factor=profit_factor(decisions),
        max_drawdown=max_drawdown(decisions),
    )

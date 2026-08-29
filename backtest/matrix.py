"""Deterministic execution of isolated backtest modes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .data_snapshot import BacktestSnapshot
from .mode import BacktestMode
from .runner import BacktestResult, BacktestRunner


@dataclass(frozen=True, slots=True)
class ModeResult:
    mode: BacktestMode
    result: BacktestResult


def run_mode_matrix(
    snapshots: Sequence[BacktestSnapshot],
    strategy_factory: Callable[[BacktestMode], Callable[[dict[str, object]], object]],
    modes: Sequence[BacktestMode] = tuple(BacktestMode),
) -> tuple[ModeResult, ...]:
    """Run each requested mode independently over the same immutable snapshots."""
    return tuple(
        ModeResult(mode, BacktestRunner(strategy_factory(mode), mode).run(snapshots))
        for mode in modes
    )

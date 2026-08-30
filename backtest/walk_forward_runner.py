"""Walk-forward execution wrapper with explicit train/test separation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from .data_snapshot import BacktestSnapshot
from .metrics import max_drawdown, profit_factor, win_rate
from .runner import BacktestRunner, BacktestResult
from .walk_forward import WalkForwardWindow, build_windows
from .mode import BacktestMode


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    window: WalkForwardWindow
    test_result: BacktestResult
    win_rate: float
    profit_factor: float
    max_drawdown: float


def run_walk_forward(
    snapshots: Sequence[BacktestSnapshot],
    strategy: Callable[[BacktestSnapshot], Any],
    train_size: int,
    test_size: int,
    mode: BacktestMode = BacktestMode.PATTERN_ONLY,
) -> tuple[WalkForwardResult, ...]:
    results: list[WalkForwardResult] = []
    for window in build_windows(snapshots, train_size, test_size):
        # Training data is deliberately not passed to the test runner. This keeps
        # the execution boundary explicit until a future fitted-model interface exists.
        test_result = BacktestRunner(strategy, mode).run(window.test)
        numeric = tuple(
            value for value in test_result.decisions
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        )
        results.append(
            WalkForwardResult(
                window=window,
                test_result=test_result,
                win_rate=win_rate(numeric),
                profit_factor=profit_factor(numeric),
                max_drawdown=max_drawdown(numeric),
            )
        )
    return tuple(results)

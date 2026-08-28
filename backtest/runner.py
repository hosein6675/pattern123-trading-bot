"""Strategy-isolated backtest runner."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data_snapshot import BacktestSnapshot


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Deterministic decisions produced from point-in-time snapshots."""

    decisions: tuple[Any, ...]
    snapshots_processed: int


class BacktestRunner:
    """Run a strategy over ordered snapshots without mutating their context."""

    def __init__(self, strategy: Callable[[BacktestSnapshot], Any]) -> None:
        self._strategy = strategy

    def run(
        self, snapshots: Iterable[BacktestSnapshot], as_of: datetime | None = None
    ) -> BacktestResult:
        ordered = tuple(snapshots)
        previous: datetime | None = None
        decisions: list[Any] = []
        for snapshot in ordered:
            if previous is not None and snapshot.timestamp < previous:
                raise ValueError("snapshots must be ordered by timestamp")
            if as_of is not None:
                snapshot.with_context_until(as_of)
            decisions.append(self._strategy(snapshot))
            previous = snapshot.timestamp
        return BacktestResult(tuple(decisions), len(ordered))

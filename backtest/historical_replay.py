"""Validated historical replay orchestration."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data_snapshot import BacktestSnapshot
from .data_quality import validate_snapshots
from .runner import BacktestResult, BacktestRunner
from .mode import BacktestMode


@dataclass(frozen=True, slots=True)
class HistoricalReplayResult:
    result: BacktestResult
    first_timestamp: datetime | None
    last_timestamp: datetime | None


def run_historical_replay(
    snapshots: Iterable[BacktestSnapshot],
    strategy: Callable[[BacktestSnapshot], Any],
    mode: BacktestMode = BacktestMode.PATTERN_ONLY,
) -> HistoricalReplayResult:
    ordered = tuple(snapshots)
    validate_snapshots(ordered)
    result = BacktestRunner(strategy, mode).run(ordered)
    timestamps = tuple(snapshot.timestamp for snapshot in ordered)
    return HistoricalReplayResult(
        result=result,
        first_timestamp=timestamps[0] if timestamps else None,
        last_timestamp=timestamps[-1] if timestamps else None,
    )

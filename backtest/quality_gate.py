"""Pre-execution validation for historical backtest snapshots."""

from __future__ import annotations

from collections.abc import Iterable

from .data_snapshot import BacktestSnapshot


def validate_snapshots(snapshots: Iterable[BacktestSnapshot]) -> tuple[BacktestSnapshot, ...]:
    ordered = tuple(snapshots)
    previous = None
    seen = set()
    for snapshot in ordered:
        if snapshot.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if snapshot.timestamp in seen:
            raise ValueError("duplicate snapshot timestamp")
        if previous is not None and snapshot.timestamp < previous:
            raise ValueError("snapshots must be ordered by timestamp")
        if snapshot.price < 0:
            raise ValueError("price must be non-negative")
        seen.add(snapshot.timestamp)
        previous = snapshot.timestamp
    return ordered

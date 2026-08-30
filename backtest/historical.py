"""Point-in-time historical-data loading with hard leakage boundaries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Protocol, TypeVar

from .data_snapshot import BacktestSnapshot

T = TypeVar("T")


class HistoricalAdapter(Protocol[T]):
    def load(self, start: datetime, end: datetime) -> Iterable[T]: ...


def load_snapshots(
    adapter: HistoricalAdapter[T],
    start: datetime,
    end: datetime,
    to_snapshot: Callable[[T], BacktestSnapshot],
) -> tuple[BacktestSnapshot, ...]:
    """Load [start, end) data and reject records outside the requested window."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must be timezone-aware")
    if end <= start:
        raise ValueError("end must be after start")

    snapshots = tuple(to_snapshot(record) for record in adapter.load(start, end))
    for snapshot in snapshots:
        snapshot.with_context_until(end)
        if snapshot.timestamp < start:
            raise ValueError("adapter returned data before requested start")
        if snapshot.timestamp >= end:
            raise ValueError("adapter returned data at or after requested end")
    return tuple(sorted(snapshots, key=lambda item: item.timestamp))

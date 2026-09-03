"""Quality gates for historical market data before replay/backtest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from .data_snapshot import BacktestSnapshot


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    rows: int
    ordered: bool
    duplicate_timestamps: int
    missing_required: int

    @property
    def valid(self) -> bool:
        return self.rows > 0 and self.ordered and self.duplicate_timestamps == 0 and self.missing_required == 0


def validate_rows(rows: Iterable[dict], required: tuple[str, ...] = ("timestamp", "price")) -> DataQualityReport:
    count = duplicates = missing = 0
    ordered = True
    previous: datetime | None = None
    seen: set[datetime] = set()
    for row in rows:
        count += 1
        if any(key not in row or row[key] in (None, "") for key in required):
            missing += 1
            continue
        timestamp = row["timestamp"]
        if not isinstance(timestamp, datetime):
            missing += 1
            continue
        if previous is not None and timestamp < previous:
            ordered = False
        if timestamp in seen:
            duplicates += 1
        seen.add(timestamp)
        previous = timestamp
    return DataQualityReport(count, ordered, duplicates, missing)


def validate_snapshots(snapshots: Iterable[BacktestSnapshot]) -> None:
    ordered = tuple(snapshots)
    if not ordered:
        raise ValueError("snapshots must not be empty")
    previous: datetime | None = None
    seen: set[datetime] = set()
    for snapshot in ordered:
        if previous is not None and snapshot.timestamp < previous:
            raise ValueError("snapshots must be ordered by timestamp")
        if snapshot.timestamp in seen:
            raise ValueError("snapshot timestamps must be unique")
        seen.add(snapshot.timestamp)
        previous = snapshot.timestamp

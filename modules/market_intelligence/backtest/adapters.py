from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Protocol, TypeVar

from .replay import ReplayEvent


T = TypeVar("T")


class HistoricalDataAdapter(Protocol[T]):
    """Adapter contract for external historical market-data providers."""

    def load(self, start: datetime, end: datetime) -> Iterable[T]: ...


@dataclass(frozen=True)
class AdapterEvent:
    timestamp: datetime
    source: str
    payload: object


class ReplayAdapter(Generic[T]):
    """Converts provider records into replay events without changing payload semantics."""

    def __init__(self, source: str, records: Iterable[T]):
        self.source = source
        self.records = tuple(records)

    def events(self, timestamp_of) -> Iterator[ReplayEvent]:
        for record in sorted(self.records, key=timestamp_of):
            yield ReplayEvent(timestamp=timestamp_of(record), payload=record)

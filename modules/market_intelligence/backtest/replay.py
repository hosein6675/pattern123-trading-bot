from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReplayEvent:
    timestamp: datetime
    payload: object


class HistoricalReplay:
    """Deterministic chronological replay of historical events."""

    def __init__(self, events: Iterable[ReplayEvent]):
        self._events = tuple(events)

    def events(self) -> Iterator[ReplayEvent]:
        yield from sorted(self._events, key=lambda event: event.timestamp)

    def run(self, on_event: Callable[[ReplayEvent], None]) -> int:
        count = 0
        for event in self.events():
            on_event(event)
            count += 1
        return count

"""Live Level-2 adapter boundary.

No broker/platform SDK is bundled here. A provider implementation must explicitly
supply normalized snapshots; otherwise Level-2 remains unavailable/disabled.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol

from .models import OrderFlowSnapshot


class Level2Provider(Protocol):
    def snapshots(self) -> Iterable[OrderFlowSnapshot]: ...


@dataclass(frozen=True, slots=True)
class LiveOrderFlowAdapter:
    provider: Level2Provider
    enabled: bool = False

    def stream(self) -> Iterator[OrderFlowSnapshot]:
        if not self.enabled:
            return iter(())
        return iter(self.provider.snapshots())


def validate_snapshot(snapshot: OrderFlowSnapshot) -> OrderFlowSnapshot:
    if not snapshot.provider.strip():
        raise ValueError("provider is required")
    if not snapshot.instrument.strip():
        raise ValueError("instrument is required")
    if snapshot.timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    if snapshot.bid < 0 or snapshot.ask < 0:
        raise ValueError("bid and ask must be non-negative")
    if snapshot.bid_size < 0 or snapshot.ask_size < 0 or snapshot.volume < 0:
        raise ValueError("sizes and volume must be non-negative")
    return snapshot

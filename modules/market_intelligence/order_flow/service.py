"""Provider-neutral service for optional order-flow observations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from .models import OrderFlowSnapshot


class OrderFlowProvider(Protocol):
    """Adapter contract for CME/Level-2/Delta data sources."""

    def fetch(
        self, instrument: str, since: datetime | None = None
    ) -> Iterable[OrderFlowSnapshot]: ...


class OrderFlowService:
    """Expose order-flow data only when explicitly enabled by the caller."""

    def __init__(self, providers: Iterable[OrderFlowProvider] = (), enabled: bool = False) -> None:
        self._providers = tuple(providers)
        self._enabled = bool(enabled)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)

    def snapshots(
        self, instrument: str, since: datetime | None = None
    ) -> tuple[OrderFlowSnapshot, ...]:
        if not instrument.strip():
            raise ValueError("instrument must not be empty")
        if not self._enabled:
            return ()
        snapshots = tuple(
            snapshot
            for provider in self._providers
            for snapshot in provider.fetch(instrument, since)
        )
        for snapshot in snapshots:
            snapshot.validate()
        return snapshots

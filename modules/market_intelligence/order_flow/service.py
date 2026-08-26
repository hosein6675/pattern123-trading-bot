"""Service boundary for optional order-flow providers.

This module intentionally contains no Pattern123, price-action, MACD, or
trade-execution logic. Providers can be added later without coupling their
market-data feed to the strategy engine.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import OrderFlowSnapshot


class OrderFlowProvider(Protocol):
    """Adapter contract for CME/Level-2 data providers."""

    def snapshot(self, instrument: str) -> OrderFlowSnapshot: ...


class OrderFlowService:
    """Provider-independent facade for the platform's order-flow data layer."""

    def __init__(self, providers: Iterable[OrderFlowProvider] = ()) -> None:
        self._providers = tuple(providers)

    @property
    def enabled(self) -> bool:
        return bool(self._providers)

    def snapshots(self, instrument: str) -> tuple[OrderFlowSnapshot, ...]:
        if not instrument.strip():
            raise ValueError("instrument must not be empty")
        snapshots = tuple(provider.snapshot(instrument) for provider in self._providers)
        for snapshot in snapshots:
            snapshot.validate()
        return snapshots

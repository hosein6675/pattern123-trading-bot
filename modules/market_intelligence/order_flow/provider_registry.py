"""Explicit registry for real Level-2 providers.

The registry intentionally contains no synthetic/default provider. A provider must
be registered by the runtime integration layer before Level-2 can be enabled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .live_adapter import Level2Provider, LiveOrderFlowAdapter
from .settings import OrderFlowSettings


@dataclass(slots=True)
class Level2ProviderRegistry:
    _providers: dict[str, Level2Provider] = field(default_factory=dict)

    def register(self, name: str, provider: Level2Provider) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("provider name is required")
        if key in self._providers:
            raise ValueError(f"provider already registered: {name}")
        self._providers[key] = provider

    def create_adapter(self, name: str, settings: OrderFlowSettings) -> LiveOrderFlowAdapter:
        settings.validate()
        key = name.strip().lower()
        if settings.enabled and key not in self._providers:
            raise LookupError(f"live Level-2 provider is not registered: {name}")
        provider = self._providers.get(key)
        if provider is None:
            return LiveOrderFlowAdapter(_EmptyProvider(), enabled=False)
        return LiveOrderFlowAdapter(provider, enabled=settings.enabled)


class _EmptyProvider:
    def snapshots(self):
        return iter(())

"""Optional order-flow provider boundary.

Providers are deliberately isolated from strategy and execution logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable

from .models import OrderFlowSnapshot


class OrderFlowProvider(ABC):
    """Provider-neutral interface for Level-2/CME-derived observations."""

    @abstractmethod
    def fetch(self, instrument: str, since: datetime | None = None) -> Iterable[OrderFlowSnapshot]:
        """Return observations without applying trading-strategy decisions."""


class DisabledOrderFlowProvider(OrderFlowProvider):
    """Safe default: no external order-flow data is consumed."""

    def fetch(self, instrument: str, since: datetime | None = None) -> Iterable[OrderFlowSnapshot]:
        return ()

"""Time-safe snapshots for isolated backtest inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class BacktestSnapshot:
    """Immutable point-in-time inputs; future observations are rejected."""

    timestamp: datetime
    price: float
    pattern_data: Mapping[str, Any]
    news_data: tuple[Any, ...] = ()
    order_flow_data: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

    def with_context_until(self, as_of: datetime) -> "BacktestSnapshot":
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        if self.timestamp > as_of:
            raise ValueError("snapshot cannot contain future data")
        return self

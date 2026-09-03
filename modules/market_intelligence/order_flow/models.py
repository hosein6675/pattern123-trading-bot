"""Canonical data contracts for optional CME/Level-2 order-flow intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Optional


@dataclass(frozen=True, slots=True)
class OrderFlowSnapshot:
    """Provider-neutral snapshot; no trading-strategy semantics are attached."""

    provider: str
    instrument: str
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    delta: Optional[float] = None
    cumulative_delta: Optional[float] = None
    volume: Optional[float] = None
    source_sequence: Optional[int] = None

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if not self.instrument.strip():
            raise ValueError("instrument must not be empty")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        for name in ("bid", "ask", "bid_size", "ask_size", "delta", "cumulative_delta", "volume"):
            value = getattr(self, name)
            if value is not None and not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("bid cannot exceed ask")
        for name in ("bid_size", "ask_size", "volume"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")

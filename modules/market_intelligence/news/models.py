"""Domain models for scheduled market-news intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class NewsImpact(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NewsBias(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    name: str
    scheduled_at: datetime
    impact: NewsImpact
    currency: str


@dataclass(frozen=True)
class NewsSignal:
    event_id: str
    observed_at: datetime
    bias: NewsBias
    confidence: float
    source_count: int
    rationale: str = ""

    def validate(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.source_count < 0:
            raise ValueError("source_count must not be negative")

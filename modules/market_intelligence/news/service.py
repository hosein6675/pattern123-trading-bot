"""Optional news-intelligence service; never changes strategy decisions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from .models import NewsBias, NewsEvent, NewsSignal


class NewsSource(Protocol):
    def signals(self, event: NewsEvent) -> list[NewsSignal]: ...


class NewsIntelligenceService:
    """Collect signals in a bounded pre-event window when explicitly requested."""

    def __init__(self, sources: list[NewsSource] | None = None) -> None:
        self._sources = list(sources or [])

    def sources(self) -> int:
        return len(self._sources)

    def collect_pre_event(
        self, event: NewsEvent, now: datetime | None = None, minutes_before: int = 10
    ) -> tuple[NewsSignal, ...]:
        if minutes_before < 0:
            raise ValueError("minutes_before must not be negative")
        current = now or datetime.now(timezone.utc)
        window_start = event.scheduled_at - timedelta(minutes=minutes_before)
        if not window_start <= current <= event.scheduled_at:
            return ()
        signals = tuple(signal for source in self._sources for signal in source.signals(event))
        for signal in signals:
            signal.validate()
        return signals

    @staticmethod
    def aggregate(signals: list[NewsSignal] | tuple[NewsSignal, ...]) -> NewsSignal | None:
        if not signals:
            return None
        total = sum(signal.confidence for signal in signals)
        bullish = sum(signal.confidence for signal in signals if signal.bias is NewsBias.BULLISH)
        bearish = sum(signal.confidence for signal in signals if signal.bias is NewsBias.BEARISH)
        if bullish == bearish:
            bias = NewsBias.NEUTRAL
        else:
            bias = NewsBias.BULLISH if bullish > bearish else NewsBias.BEARISH
        confidence = max(bullish, bearish) / total if total else 0.0
        result = NewsSignal(
            event_id=signals[0].event_id,
            observed_at=max(signal.observed_at for signal in signals),
            bias=bias,
            confidence=confidence,
            source_count=len(signals),
            rationale="Weighted aggregation of independent source signals.",
        )
        result.validate()
        return result

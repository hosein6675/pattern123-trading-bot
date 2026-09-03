from datetime import datetime, timedelta, timezone

import pytest

from modules.market_intelligence.news.models import NewsBias, NewsEvent, NewsImpact, NewsSignal
from modules.market_intelligence.news.service import NewsIntelligenceService


class StubSource:
    def __init__(self, signals):
        self._signals = signals

    def signals(self, event):
        return self._signals


def event():
    return NewsEvent(
        event_id="nfp-2026-01",
        name="NFP",
        scheduled_at=datetime(2026, 1, 9, 13, 30, tzinfo=timezone.utc),
        impact=NewsImpact.CRITICAL,
        currency="USD",
    )


def test_pre_event_window_is_strictly_bounded():
    e = event()
    signal = NewsSignal(e.event_id, e.scheduled_at - timedelta(minutes=5), NewsBias.BULLISH, 0.8, 1)
    service = NewsIntelligenceService([StubSource([signal])])

    assert service.collect_pre_event(e, e.scheduled_at - timedelta(minutes=10)) == (signal,)
    assert service.collect_pre_event(e, e.scheduled_at - timedelta(minutes=11)) == ()
    assert service.collect_pre_event(e, e.scheduled_at + timedelta(seconds=1)) == ()


def test_disabled_by_empty_sources_and_no_lookahead():
    e = event()
    service = NewsIntelligenceService()
    assert service.sources() == 0
    assert service.collect_pre_event(e, e.scheduled_at - timedelta(minutes=1)) == ()


def test_aggregate_uses_confidence_weights():
    e = event()
    signals = (
        NewsSignal(e.event_id, e.scheduled_at - timedelta(minutes=4), NewsBias.BULLISH, 0.9, 1),
        NewsSignal(e.event_id, e.scheduled_at - timedelta(minutes=3), NewsBias.BEARISH, 0.2, 1),
    )
    result = NewsIntelligenceService.aggregate(signals)
    assert result is not None
    assert result.bias is NewsBias.BULLISH
    assert result.confidence == pytest.approx(0.9 / 1.1)
    assert result.source_count == 2


def test_invalid_signal_is_rejected():
    e = event()
    invalid = NewsSignal(e.event_id, e.scheduled_at, NewsBias.BULLISH, 1.5, 1)
    service = NewsIntelligenceService([StubSource([invalid])])
    with pytest.raises(ValueError, match="confidence"):
        service.collect_pre_event(e, e.scheduled_at - timedelta(minutes=1))

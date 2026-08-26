from datetime import datetime, timezone

from modules.market_intelligence.backtest.replay import HistoricalReplay, ReplayEvent


def test_replay_is_chronological_and_deterministic():
    events = [
        ReplayEvent(datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc), "b"),
        ReplayEvent(datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc), "a"),
    ]
    received = []
    count = HistoricalReplay(events).run(lambda event: received.append(event.payload))

    assert count == 2
    assert received == ["a", "b"]

from modules.journal import JournalEngine
from modules.mt5_journal_gateway import MT5JournalGateway


def test_mt5_journal_accepts_account_and_deduplicates_deals():
    journal = JournalEngine()
    gateway = MT5JournalGateway(journal=journal, max_age_seconds=120)
    import time
    now = int(time.time())
    payload = {
        "source": "mt5",
        "demo_mode": False,
        "observed_at": now,
        "account": {"balance": 1000, "equity": 995},
        "events": [{
            "event_id": "123",
            "type": "deal",
            "time": now,
            "deal_id": "123",
            "position_id": "456",
            "price": 1.1,
            "volume": 0.1,
        }],
    }
    ok, reason, counts = gateway.ingest(payload)
    assert ok and reason == "accepted"
    assert counts["events_accepted"] == 1
    ok, _, counts = gateway.ingest(payload)
    assert ok
    assert counts["events_skipped"] == 1
    assert len(journal.get_events("456")) == 1
    assert len(journal.get_account_snapshots()) == 2


def test_mt5_journal_rejects_non_mt5_and_stale():
    journal = JournalEngine()
    gateway = MT5JournalGateway(journal=journal, max_age_seconds=1)
    import time
    now = int(time.time())
    bad = {"source": "demo", "demo_mode": True, "observed_at": now}
    assert gateway.ingest(bad)[0] is False
    stale = {
        "source": "mt5", "demo_mode": False, "observed_at": now - 10,
        "account": {"balance": 1000, "equity": 1000}, "events": [],
    }
    assert gateway.ingest(stale)[0] is False

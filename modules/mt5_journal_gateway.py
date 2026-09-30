from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from modules.journal import JournalEngine

_REQUIRED_ACCOUNT = ("balance", "equity")


class MT5JournalGateway:
    """Accept only authenticated, current MT5 account/lifecycle observations."""

    def __init__(self, journal: JournalEngine | None = None, max_age_seconds: int = 120):
        self.journal = journal or JournalEngine()
        self.max_age_seconds = max_age_seconds

    def ingest(self, payload: dict[str, Any]) -> tuple[bool, str, dict[str, int]]:
        if not isinstance(payload, dict):
            return False, "Invalid MT5 journal payload", {}
        if payload.get("source") != "mt5" or payload.get("demo_mode") is not False:
            return False, "MT5 provenance required", {}
        observed_at = self._observed_at(payload)
        if observed_at is None:
            return False, "Invalid MT5 observation timestamp", {}
        now = int(datetime.now(timezone.utc).timestamp())
        if abs(now - observed_at) > self.max_age_seconds:
            return False, "Stale MT5 journal payload", {}

        account = payload.get("account")
        if not isinstance(account, dict) or any(k not in account for k in _REQUIRED_ACCOUNT):
            return False, "MT5 account snapshot is required", {}

        try:
            self.journal.record_account_snapshot(
                float(account["balance"]),
                float(account["equity"]),
                observed_at=datetime.fromtimestamp(observed_at, timezone.utc).isoformat(),
                peak_equity=account.get("peak_equity"),
                drawdown_percent=account.get("drawdown_percent"),
                source="mt5",
                raw=account,
            )
        except (TypeError, ValueError):
            return False, "Invalid MT5 account snapshot", {}

        accepted = 0
        skipped = 0
        for event in payload.get("events", []):
            if not isinstance(event, dict):
                return False, "Invalid MT5 lifecycle event", {}
            source_id = str(event.get("event_id", ""))
            if not source_id:
                return False, "Lifecycle event id is required", {}
            if self.journal.has_source_event(source_id):
                skipped += 1
                continue
            try:
                event_time = int(event.get("time", observed_at))
            except (TypeError, ValueError):
                return False, "Invalid MT5 lifecycle event timestamp", {}
            if abs(now - event_time) > self.max_age_seconds:
                return False, "Stale MT5 lifecycle event", {}
            trade_id = str(event.get("position_id") or event.get("deal_id") or source_id)
            self.journal.record_event(
                trade_id,
                str(event.get("type", "mt5_deal")),
                event_time=datetime.fromtimestamp(event_time, timezone.utc).isoformat(),
                price=event.get("price"),
                old_value=event.get("old_value"),
                new_value=event.get("new_value"),
                source_event_id=source_id,
                reason=str(event.get("reason", "")),
                actor="mt5",
                snapshot=event,
            )
            accepted += 1

        return True, "accepted", {
            "account_snapshots": 1,
            "events_accepted": accepted,
            "events_skipped": skipped,
        }

    @staticmethod
    def _observed_at(payload: dict[str, Any]) -> int | None:
        try:
            value = int(payload.get("observed_at", 0))
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

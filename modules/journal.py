from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone

SCHEMA_VERSION = 1
_MEMORY_URI = "file:pattern123_journal?mode=memory&cache=shared"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(v):
    if is_dataclass(v):
        v = asdict(v)
    return json.dumps(v, ensure_ascii=False, default=str, sort_keys=True)


@dataclass(frozen=True)
class TradeRecord:
    trade_id: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: float
    exit_price: float | None
    stop_loss: float
    take_profit: float
    entry_time: str
    exit_time: str | None
    result: str
    profit_loss: float | None
    reason: str
    analysis: str
    risk_reward: float | None = None
    volume: float = 0.0
    risk_percent: float | None = None
    risk_amount: float | None = None
    strategy_version: str = "unknown"
    journal_schema_version: int = SCHEMA_VERSION


class JournalEngine:
    """Append-oriented lifecycle journal. Raw MT5 observations are retained."""

    def __init__(self, db_path=None):
        requested_path = db_path or os.getenv("JOURNAL_DB_PATH", ":memory:")
        self._memory = requested_path == ":memory:"
        self.db_path = _MEMORY_URI if self._memory else requested_path
        self._lock = threading.RLock()
        self._anchor = None
        self._init()

    def _db(self):
        c = sqlite3.connect(self.db_path, check_same_thread=False, uri=self._memory)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._lock:
            if self._memory:
                self._anchor = self._db()
                c = self._anchor
                c.execute("PRAGMA journal_mode=MEMORY")
            else:
                c = self._db()
            try:
                c.executescript(
                    """CREATE TABLE IF NOT EXISTS trades(
                    trade_id TEXT PRIMARY KEY,position_id TEXT,symbol TEXT NOT NULL,direction TEXT NOT NULL,timeframe TEXT,status TEXT NOT NULL,
                    entry_time TEXT,exit_time TEXT,entry_price REAL,exit_price REAL,volume REAL,stop_loss REAL,take_profit REAL,risk_reward REAL,
                    risk_percent REAL,risk_amount REAL,gross_pnl REAL,net_pnl REAL,commission REAL,swap REAL,fees REAL,spread_cost REAL,slippage REAL,
                    mae_r REAL,mfe_r REAL,exit_reason TEXT,entry_reason TEXT,strategy_version TEXT,bot_version TEXT,mt5_account TEXT,broker TEXT,
                    magic_number TEXT,compliance_json TEXT,entry_snapshot_json TEXT,exit_snapshot_json TEXT,money_management_json TEXT,created_at TEXT,updated_at TEXT);
                    CREATE TABLE IF NOT EXISTS trade_events(
                    event_id TEXT PRIMARY KEY,trade_id TEXT,event_time TEXT,event_type TEXT,price REAL,old_value_json TEXT,new_value_json TEXT,
                    reason TEXT,actor TEXT,snapshot_json TEXT);
                    CREATE TABLE IF NOT EXISTS account_snapshots(
                    snapshot_id TEXT PRIMARY KEY,observed_at TEXT,balance REAL,equity REAL,peak_equity REAL,drawdown_percent REAL,source TEXT,raw_json TEXT);
                    CREATE INDEX IF NOT EXISTS idx_events_trade ON trade_events(trade_id,event_time);
                    CREATE INDEX IF NOT EXISTS idx_account_time ON account_snapshots(observed_at);"""
                )
                columns = {row[1] for row in c.execute("PRAGMA table_info(trade_events)")}
                if "source_event_id" not in columns:
                    c.execute("ALTER TABLE trade_events ADD COLUMN source_event_id TEXT")
                c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_events_source ON trade_events(source_event_id) WHERE source_event_id IS NOT NULL")
            finally:
                if not self._memory:
                    c.close()

    def record_trade_open(self, trade_id=None, **d):
        tid = trade_id or uuid.uuid4().hex
        now = _now()
        for k in ("symbol", "direction"):
            if k not in d:
                raise ValueError(f"missing trade field: {k}")
        with self._lock, self._db() as c:
            c.execute(
                """INSERT INTO trades(trade_id,position_id,symbol,direction,timeframe,status,entry_time,entry_price,volume,stop_loss,take_profit,
                risk_reward,risk_percent,risk_amount,entry_reason,strategy_version,bot_version,mt5_account,broker,magic_number,compliance_json,
                entry_snapshot_json,money_management_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    tid, str(d.get("position_id", "")), str(d["symbol"]).upper(),
                    str(d["direction"]).lower(), d.get("timeframe"), "open",
                    d.get("entry_time", now), d.get("entry_price"), d.get("volume", 0),
                    d.get("stop_loss"), d.get("take_profit"), d.get("risk_reward"),
                    d.get("risk_percent"), d.get("risk_amount"),
                    d.get("entry_reason", d.get("reason", "")),
                    d.get("strategy_version", "unknown"), d.get("bot_version", "unknown"),
                    d.get("mt5_account", ""), d.get("broker", ""), d.get("magic_number", ""),
                    _json(d.get("compliance", {})), _json(d.get("entry_snapshot", {})),
                    _json(d.get("money_management", {})), now, now,
                ),
            )
        return tid

    def record_event(self, trade_id, event_type, **d):
        eid = uuid.uuid4().hex
        with self._lock, self._db() as c:
            c.execute(
                """INSERT OR IGNORE INTO trade_events(event_id,trade_id,event_time,event_type,price,old_value_json,new_value_json,source_event_id,reason,actor,snapshot_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    eid, trade_id, d.get("event_time", _now()), event_type, d.get("price"),
                    _json(d.get("old_value")), _json(d.get("new_value")), d.get("source_event_id"),
                    d.get("reason", ""), d.get("actor", "system"), _json(d.get("snapshot")),
                ),
            )
        return eid

    def has_source_event(self, source_event_id):
        if not source_event_id:
            return False
        with self._lock, self._db() as c:
            row = c.execute("SELECT 1 FROM trade_events WHERE source_event_id=?", (str(source_event_id),)).fetchone()
        return row is not None

    def record_trade_close(self, trade_id, **d):
        now = _now()
        with self._lock, self._db() as c:
            cur = c.execute(
                """UPDATE trades SET status='closed',exit_time=?,exit_price=?,gross_pnl=?,net_pnl=?,commission=?,swap=?,fees=?,
                spread_cost=?,slippage=?,mae_r=?,mfe_r=?,exit_reason=?,exit_snapshot_json=?,compliance_json=?,updated_at=?
                WHERE trade_id=? AND status='open'""",
                (
                    d.get("exit_time", now), d.get("exit_price"),
                    d.get("gross_pnl", d.get("profit_loss")), d.get("net_pnl", d.get("profit_loss")),
                    d.get("commission", 0), d.get("swap", 0), d.get("fees", 0),
                    d.get("spread_cost", 0), d.get("slippage", 0), d.get("mae_r"), d.get("mfe_r"),
                    d.get("exit_reason", d.get("reason", "")), _json(d.get("exit_snapshot", {})),
                    _json(d.get("compliance", {})), now, trade_id,
                ),
            )
        if not cur.rowcount:
            return False
        self.record_event(
            trade_id, "close", event_time=d.get("exit_time", now), price=d.get("exit_price"),
            reason=d.get("exit_reason", d.get("reason", "")), actor=d.get("actor", "system"),
            snapshot=d.get("exit_snapshot", {}),
        )
        return True

    def record_account_snapshot(self, balance, equity, **d):
        if d.get("source", "mt5") != "mt5":
            raise ValueError("account snapshots must identify MT5 provenance")
        sid = uuid.uuid4().hex
        with self._lock, self._db() as c:
            c.execute(
                """INSERT INTO account_snapshots(snapshot_id,observed_at,balance,equity,peak_equity,drawdown_percent,source,raw_json)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    sid, d.get("observed_at", _now()), float(balance), float(equity),
                    d.get("peak_equity"), d.get("drawdown_percent"), "mt5", _json(d.get("raw", {})),
                ),
            )
        return sid

    def get_trade(self, trade_id):
        with self._lock, self._db() as c:
            r = c.execute("SELECT * FROM trades WHERE trade_id=?", (trade_id,)).fetchone()
        return dict(r) if r else None

    def get_history(self, limit=500):
        with self._lock, self._db() as c:
            r = c.execute(
                "SELECT * FROM trades ORDER BY COALESCE(entry_time,created_at) DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
        return [dict(x) for x in r]

    def get_events(self, trade_id):
        with self._lock, self._db() as c:
            r = c.execute(
                "SELECT * FROM trade_events WHERE trade_id=? ORDER BY event_time,event_id",
                (trade_id,),
            ).fetchall()
        return [dict(x) for x in r]

    def get_account_snapshots(self, limit=5000):
        with self._lock, self._db() as c:
            r = c.execute(
                "SELECT * FROM account_snapshots ORDER BY observed_at LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
        return [dict(x) for x in r]

    def create_trade(
        self, symbol, timeframe, direction, entry_price, exit_price, stop_loss,
        take_profit, result, profit_loss, reason, analysis
    ):
        tid = self.record_trade_open(
            symbol=symbol, timeframe=timeframe, direction=direction,
            entry_price=entry_price, stop_loss=stop_loss, take_profit=take_profit,
            entry_reason=reason, entry_snapshot={"analysis": analysis},
        )
        self.record_trade_close(
            tid, exit_price=exit_price, profit_loss=profit_loss,
            exit_reason=reason, exit_snapshot={"analysis": analysis},
        )
        return self.get_trade(tid)

    def add_trade(self, trade):
        return self.record_trade_open(
            **(asdict(trade) if is_dataclass(trade) else dict(trade))
        )

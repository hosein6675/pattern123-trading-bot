from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass
class TradeRecord:
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
    profit_loss: float
    reason: str
    analysis: str
    trade_id: str | None = None
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    risk_percent: float = 0.0
    reward_risk: float = 0.0
    strategy_version: str = "Pattern123 V1"
    market_context: str = ""
    mistakes: list[str] = field(default_factory=list)
    ai_review: str = ""


class JournalEngine:
    """Persistent trade journal with lifecycle updates and batch analytics."""

    def __init__(self, db_path: str | Path = "data/journal.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY, payload TEXT NOT NULL, entry_time TEXT NOT NULL,
                exit_time TEXT, result TEXT NOT NULL, profit_loss REAL NOT NULL,
                symbol TEXT NOT NULL, direction TEXT NOT NULL, timeframe TEXT NOT NULL
            )""")
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_trade(self, trade: TradeRecord) -> TradeRecord:
        if not trade.trade_id:
            trade.trade_id = f"TRD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO trades(trade_id,payload,entry_time,exit_time,result,profit_loss,symbol,direction,timeframe) VALUES(?,?,?,?,?,?,?,?,?)",
                (trade.trade_id, json.dumps(asdict(trade), ensure_ascii=False), trade.entry_time, trade.exit_time,
                 trade.result, trade.profit_loss, trade.symbol, trade.direction, trade.timeframe),
            )
            conn.commit()
        return trade

    def create_trade(self, symbol, timeframe, direction, entry_price, exit_price=None,
                     stop_loss=0.0, take_profit=0.0, result="OPEN", profit_loss=0.0,
                     reason="", analysis="", entry_time=None, exit_time=None,
                     positive_factors=None, negative_factors=None, risk_percent=0.0,
                     reward_risk=0.0, strategy_version="Pattern123 V1", market_context="",
                     mistakes=None, ai_review=""):
        trade = TradeRecord(
            symbol=str(symbol).upper(), timeframe=str(timeframe).upper(), direction=str(direction).lower(),
            entry_price=float(entry_price), exit_price=None if exit_price is None else float(exit_price),
            stop_loss=float(stop_loss), take_profit=float(take_profit),
            entry_time=entry_time or self._now(), exit_time=exit_time,
            result=str(result).upper(), profit_loss=float(profit_loss), reason=str(reason), analysis=str(analysis),
            positive_factors=list(positive_factors or []), negative_factors=list(negative_factors or []),
            risk_percent=float(risk_percent), reward_risk=float(reward_risk), strategy_version=str(strategy_version),
            market_context=str(market_context), mistakes=list(mistakes or []), ai_review=str(ai_review),
        )
        return self.add_trade(trade)

    def update_trade(self, trade_id: str, **changes: Any) -> TradeRecord | None:
        trade = self.get_trade(trade_id)
        if trade is None:
            return None
        for key, value in changes.items():
            if hasattr(trade, key):
                setattr(trade, key, value)
        return self.add_trade(trade)

    def get_trade(self, trade_id: str) -> TradeRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM trades WHERE trade_id=?", (trade_id,)).fetchone()
        return TradeRecord(**json.loads(row["payload"])) if row else None

    def get_history(self, limit: int | None = None) -> list[TradeRecord]:
        sql = "SELECT payload FROM trades ORDER BY entry_time DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (max(1, int(limit)),)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [TradeRecord(**json.loads(row["payload"])) for row in rows]

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0])


__all__ = ["TradeRecord", "JournalEngine"]

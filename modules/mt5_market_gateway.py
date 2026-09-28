from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from modules.live_market_data import JOURNAL_TIMEFRAMES, TIMEFRAME_OPTIONS, validate_candles, validate_tick

REQUIRED_TIMEFRAMES = JOURNAL_TIMEFRAMES


class MT5MarketGateway:
    """Fail-closed in-memory bridge for snapshots pushed by the Windows MT5 EA.

    The gateway never manufactures market data. A snapshot is accepted only when
    its provenance, tick, and every required timeframe pass live-data validation.
    """

    def __init__(self, max_age_seconds: int = 120):
        self.max_age_seconds = max_age_seconds
        self._lock = Lock()
        self._snapshots: dict[str, dict[str, Any]] = {}

    def ingest(self, payload: dict[str, Any]) -> tuple[bool, str]:
        if not isinstance(payload, dict):
            return False, "Invalid MT5 payload"
        if payload.get("source") != "mt5" or payload.get("demo_mode") is not False:
            return False, "MT5 provenance required"
        symbol = str(payload.get("symbol", "")).upper()
        if not symbol:
            return False, "Symbol is required"

        tick = dict(payload.get("tick") or {})
        tick["source"] = "mt5"
        tick["demo_mode"] = False
        tick_ok, tick_reason = validate_tick(
            tick, max_age_seconds=self.max_age_seconds
        )
        if not tick_ok:
            return False, tick_reason

        raw_timeframes = payload.get("timeframes")
        if not isinstance(raw_timeframes, dict):
            return False, "MT5 timeframes are required"

        normalized: dict[str, Any] = {
            "symbol": symbol,
            "source": "mt5",
            "demo_mode": False,
            "live_tick_time": int(tick["time"]),
            "tick": {
                "bid": float(tick["bid"]),
                "ask": float(tick["ask"]),
                "time": int(tick["time"]),
            },
            "timeframes": {},
            "received_at": datetime.now(timezone.utc).isoformat(),
        }

        supplied = {str(item).upper() for item in raw_timeframes}
        if not set(REQUIRED_TIMEFRAMES).issubset(supplied):
            missing = sorted(set(REQUIRED_TIMEFRAMES) - supplied)
            return False, f"Missing journal timeframes: {missing}"
        for timeframe in supplied:
            if timeframe not in TIMEFRAME_OPTIONS:
                return False, f"Unsupported timeframe: {timeframe}"
            market = {
                "source": "mt5",
                "demo_mode": False,
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": raw_timeframes.get(timeframe),
            }
            ok, reason = validate_candles(market, timeframe)
            if not ok:
                return False, f"{timeframe}: {reason}"
            normalized["timeframes"][timeframe] = deepcopy(market["candles"])

        with self._lock:
            self._snapshots[symbol] = normalized
        return True, ""

    def get_candles(self, symbol: str, timeframe: str) -> dict[str, Any]:
        symbol = str(symbol).upper()
        timeframe = str(timeframe).upper()
        with self._lock:
            snapshot = deepcopy(self._snapshots.get(symbol))
        if not snapshot:
            return {
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "mt5",
                "demo_mode": False,
                "candles": [],
                "message": "No live MT5 snapshot received",
            }
        if timeframe not in snapshot["timeframes"]:
            return {
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "mt5",
                "demo_mode": False,
                "candles": [],
                "message": "Requested timeframe has not been received from MT5",
            }
        if timeframe not in TIMEFRAME_OPTIONS:
            return {
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "mt5",
                "demo_mode": False,
                "candles": [],
                "message": "Unsupported timeframe",
            }

        tick = {
            **snapshot["tick"],
            "source": "mt5",
            "demo_mode": False,
        }
        tick_ok, tick_reason = validate_tick(
            tick, max_age_seconds=self.max_age_seconds
        )
        if not tick_ok:
            return {
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe,
                "source": "mt5",
                "demo_mode": False,
                "candles": [],
                "message": tick_reason,
            }

        market = {
            "status": "ready",
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": snapshot["timeframes"][timeframe],
            "source": "mt5",
            "demo_mode": False,
            "live_tick_time": int(snapshot["live_tick_time"]),
        }
        candle_ok, candle_reason = validate_candles(market, timeframe)
        if not candle_ok:
            market.update({"status": "error", "candles": [], "message": candle_reason})
        return market

    def status(self, symbol: str) -> dict[str, Any]:
        symbol = str(symbol).upper()
        with self._lock:
            snapshot = deepcopy(self._snapshots.get(symbol))
        if not snapshot:
            return {"status": "unavailable", "source": "mt5", "demo_mode": False}
        tick = {**snapshot["tick"], "source": "mt5", "demo_mode": False}
        ok, reason = validate_tick(tick, max_age_seconds=self.max_age_seconds)
        return {
            "status": "ready" if ok else "stale",
            "source": "mt5",
            "demo_mode": False,
            "symbol": symbol,
            "live_tick_time": snapshot["live_tick_time"],
            "message": reason,
        }


mt5_market_gateway = MT5MarketGateway()

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import hmac
import threading
import time
import uuid

from modules.config import active_config


_ALLOWED_DIRECTIONS = {"buy", "sell"}
_MAX_TTL_SECONDS = 60


def _now() -> int:
    return int(time.time())


def _canonical(command_id, symbol, direction, volume, stop_loss, take_profit, expires_at):
    return "|".join([
        str(command_id), str(symbol).upper(), str(direction).lower(),
        f"{float(volume):.8f}", f"{float(stop_loss):.10f}",
        f"{float(take_profit):.10f}", str(int(expires_at)),
    ])


def sign_command(secret: str, command: dict) -> str:
    message = _canonical(
        command["command_id"], command["symbol"], command["direction"],
        command["volume"], command["stop_loss"], command["take_profit"],
        command["expires_at"],
    ).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_command_signature(secret: str, command: dict, signature: str) -> bool:
    if not secret or not signature:
        return False
    return hmac.compare_digest(sign_command(secret, command), signature)


@dataclass(frozen=True)
class ExecutionCommand:
    command_id: str
    symbol: str
    direction: str
    volume: float
    stop_loss: float
    take_profit: float
    issued_at: int
    expires_at: int
    status: str = "pending"
    signature: str = ""


class MT5ExecutionGateway:
    """Fail-closed, in-memory command bridge.

    This is intentionally not a durable execution queue. It is a controlled
    bridge for the MT5 acceptance/demo stage; live production execution must
    use durable state before trading is enabled.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._commands: dict[str, ExecutionCommand] = {}
        self._results: dict[str, dict] = {}

    def issue(self, symbol, direction, volume, stop_loss, take_profit, ttl_seconds=30):
        if active_config.mode != "live" or not active_config.live_trading_enabled:
            return False, "live_execution_disabled", None

        symbol = str(symbol).upper()
        direction = str(direction).lower()
        try:
            volume = float(volume)
            stop_loss = float(stop_loss)
            take_profit = float(take_profit)
        except (TypeError, ValueError):
            return False, "invalid_numeric_parameters", None

        if not active_config.is_symbol_allowed(symbol):
            return False, "symbol_not_allowed", None
        if direction not in _ALLOWED_DIRECTIONS or volume <= 0:
            return False, "invalid_order_parameters", None
        if stop_loss <= 0 or take_profit <= 0:
            return False, "invalid_protection_levels", None

        ttl = min(max(int(ttl_seconds), 5), _MAX_TTL_SECONDS)
        issued = _now()
        command = ExecutionCommand(
            command_id=uuid.uuid4().hex,
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            issued_at=issued,
            expires_at=issued + ttl,
        )
        secret = __import__("os").getenv("WEBHOOK_SECRET", "")
        if not secret:
            return False, "execution_secret_not_configured", None
        signed = ExecutionCommand(**{**asdict(command), "signature": sign_command(secret, asdict(command))})

        with self._lock:
            self._commands[signed.command_id] = signed
        return True, "queued", asdict(signed)

    def pending(self, symbol=None):
        now = _now()
        with self._lock:
            self._expire(now)
            values = [
                asdict(c) for c in self._commands.values()
                if c.status == "pending" and (symbol is None or c.symbol == str(symbol).upper())
            ]
        return values

    def accept_result(self, result: dict):
        command_id = str(result.get("command_id", ""))
        if not command_id:
            return False, "missing_command_id"
        try:
            timestamp = int(result.get("timestamp", 0))
        except (TypeError, ValueError):
            return False, "invalid_timestamp"
        if abs(_now() - timestamp) > 120:
            return False, "stale_result"

        secret = __import__("os").getenv("WEBHOOK_SECRET", "")
        canonical = "|".join([
            command_id, str(result.get("status", "")),
            str(result.get("order_id", "")), str(result.get("message", "")),
            str(timestamp),
        ])
        expected = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(expected, str(result.get("signature", ""))):
            return False, "invalid_signature"

        with self._lock:
            command = self._commands.get(command_id)
            if command is None:
                return False, "unknown_command"
            if command.status != "pending":
                return False, "duplicate_result"
            self._commands[command_id] = ExecutionCommand(**{**asdict(command), "status": str(result.get("status", "rejected"))})
            self._results[command_id] = dict(result)
        return True, "accepted"

    def _expire(self, now):
        for command_id, command in list(self._commands.items()):
            if command.status == "pending" and command.expires_at < now:
                self._commands[command_id] = ExecutionCommand(**{**asdict(command), "status": "expired"})

    def status(self):
        with self._lock:
            self._expire(_now())
            return {
                "pending": sum(c.status == "pending" for c in self._commands.values()),
                "completed": sum(c.status in {"executed", "rejected"} for c in self._commands.values()),
                "expired": sum(c.status == "expired" for c in self._commands.values()),
            }


mt5_execution_gateway = MT5ExecutionGateway()

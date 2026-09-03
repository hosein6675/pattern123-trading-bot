from __future__ import annotations

from dataclasses import dataclass, field
import os


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass
class TradingConfig:
    """Central runtime configuration with safe demo defaults."""

    connection: str = field(
        default_factory=lambda: os.getenv("TRADING_MODE", "demo").lower()
    )
    market: str = field(
        default_factory=lambda: os.getenv("MARKET", "forex").lower()
    )
    mode: str = field(
        default_factory=lambda: os.getenv("TRADING_MODE", "demo").lower()
    )
    symbol: str = field(
        default_factory=lambda: os.getenv("DEFAULT_SYMBOL", "EURUSD").upper()
    )
    timeframe: str = field(
        default_factory=lambda: os.getenv("DEFAULT_TIMEFRAME", "M15").upper()
    )

    # Money-management guardrails.
    risk_per_trade_percent: float = field(
        default_factory=lambda: _float_env("RISK_PER_TRADE_PERCENT", 1.0)
    )
    daily_drawdown_limit: float = field(
        default_factory=lambda: _float_env("DAILY_DRAWDOWN_LIMIT", 5.0)
    )
    max_account_drawdown: float = field(
        default_factory=lambda: _float_env("MAX_ACCOUNT_DRAWDOWN_PERCENT", 20.0)
    )
    max_open_positions: int = field(
        default_factory=lambda: _int_env("MAX_OPEN_POSITIONS", 5)
    )
    max_total_risk_percent: float = field(
        default_factory=lambda: _float_env("MAX_TOTAL_RISK_PERCENT", 3.0)
    )
    max_consecutive_losses: int = field(
        default_factory=lambda: _int_env("MAX_CONSECUTIVE_LOSSES", 3)
    )

    # Broker/position constraints. These are generic and may be overridden by
    # a live broker's symbol contract before an order is sent.
    min_lot: float = field(default_factory=lambda: _float_env("MIN_LOT", 0.01))
    max_lot: float = field(default_factory=lambda: _float_env("MAX_LOT", 100.0))
    lot_step: float = field(default_factory=lambda: _float_env("LOT_STEP", 0.01))

    allowed_symbols: set[str] = field(
        default_factory=lambda: {
            item.strip().upper()
            for item in os.getenv(
                "ALLOWED_SYMBOLS",
                "EURUSD,GBPUSD,USDJPY,XAUUSD,BTCUSD",
            ).split(",")
            if item.strip()
        }
    )

    def is_symbol_allowed(self, symbol: str) -> bool:
        return str(symbol).upper() in self.allowed_symbols

    def connect(self) -> dict[str, str]:
        return {"status": "configured", "mode": self.connection}


active_config = TradingConfig()

__all__ = ["TradingConfig", "active_config"]

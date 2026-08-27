from __future__ import annotations

from dataclasses import dataclass, field
import os


@dataclass
class TradingConfig:
    """Central runtime configuration with safe demo defaults."""

    connection: str = field(default_factory=lambda: os.getenv("TRADING_MODE", "demo"))
    timeframe: str = field(default_factory=lambda: os.getenv("DEFAULT_TIMEFRAME", "M15"))
    daily_drawdown_limit: float = 5.0
    max_open_positions: int = 5
    allowed_symbols: set[str] = field(
        default_factory=lambda: {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"}
    )

    def is_symbol_allowed(self, symbol: str) -> bool:
        return str(symbol).upper() in self.allowed_symbols

    def connect(self) -> dict[str, str]:
        return {"status": "connected", "mode": self.connection}


active_config = TradingConfig()

__all__ = ["TradingConfig", "active_config"]

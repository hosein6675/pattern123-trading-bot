from __future__ import annotations

from modules.config import active_config
from modules.trading_engine import TradingEngine


class BotController:
    def __init__(self, engine: TradingEngine | None = None):
        self.engine = engine or TradingEngine()

    def get_status(self) -> dict[str, object]:
        return {
            "market": active_config.market,
            "symbol": active_config.symbol,
            "timeframe": active_config.timeframe,
            "mode": active_config.mode,
        }

    def analyze(self, candles):
        return self.engine.analyze_market(
            active_config.symbol,
            active_config.timeframe,
            candles,
        )

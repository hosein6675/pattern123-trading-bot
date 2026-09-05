from __future__ import annotations

from modules.ai_report import AIReportEngine
from modules.config import active_config
from modules.journal_analytics import analyze as analyze_journal
from modules.telegram_permissions import TelegramPermissionManager
from modules.trading_engine import TradingEngine


class BotController:
    """Application boundary between Telegram transport and trading services."""

    def __init__(self, engine: TradingEngine | None = None, permissions: TelegramPermissionManager | None = None):
        self.engine = engine or TradingEngine()
        self.permissions = permissions or TelegramPermissionManager()
        self.ai_reports = AIReportEngine()

    def get_status(self) -> dict[str, object]:
        return {
            "market": active_config.market,
            "symbol": active_config.symbol,
            "timeframe": active_config.timeframe,
            "mode": active_config.mode,
            "live_trading_enabled": active_config.live_trading_enabled,
            "journal_trades": self.engine.journal.count(),
        }

    def analyze(self, symbol: str, timeframe: str, candles=None):
        return self.engine.analyze_market(symbol, timeframe, candles)

    def journal_history(self, limit: int = 20):
        return self.engine.journal.get_history(limit=limit)

    def journal_summary(self) -> dict[str, object]:
        return analyze_journal(self.engine.journal.get_history()) .__dict__

    def ai_report(self, category: str = "strategy_review"):
        return self.ai_reports.generate(self.engine.journal.get_history(), category)

    def open_positions(self):
        return self.engine.get_open_positions()

    def broker_status(self):
        return self.engine.orders.status()


__all__ = ["BotController"]

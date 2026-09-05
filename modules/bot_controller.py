from __future__ import annotations

from modules.ai_report import AIReportEngine
from modules.config import active_config
from modules.distribution_manager import DistributionManager
from modules.journal_analytics import analyze as analyze_journal
from modules.multi_timeframe_analysis import analyze as analyze_multi_timeframe
from modules.system_control import SystemControl
from modules.telegram_controls import TelegramSelection
from modules.telegram_permissions import TelegramPermissionManager
from modules.trading_engine import TradingEngine


class BotController:
    """Application boundary between Telegram transport and trading services."""

    def __init__(self, engine: TradingEngine | None = None, permissions: TelegramPermissionManager | None = None):
        self.engine = engine or TradingEngine()
        self.permissions = permissions or TelegramPermissionManager()
        self.ai_reports = AIReportEngine()
        self.distribution = DistributionManager()
        self.system = SystemControl()
        for module in ("telegram", "trading_engine", "journal", "distribution", "ai"):
            self.system.heartbeat(module, "ready")

    def get_status(self) -> dict[str, object]:
        return {"market": active_config.market, "symbol": active_config.symbol, "timeframe": active_config.timeframe,
                "mode": active_config.mode, "live_trading_enabled": active_config.live_trading_enabled,
                "journal_trades": self.engine.journal.count(), "system": self.system.snapshot()}

    def analyze(self, symbol: str, timeframe: str, candles=None):
        return self.engine.analyze_market(symbol, timeframe, candles)

    def analyze_multi_timeframe(self, symbol: str, selection: TelegramSelection):
        return analyze_multi_timeframe(self.engine, symbol, selection)

    def journal_history(self, limit: int = 20):
        return self.engine.journal.get_history(limit=limit)

    def journal_summary(self):
        return analyze_journal(self.engine.journal.get_history())

    def ai_report(self, category: str = "strategy_review"):
        return self.ai_reports.generate(self.engine.journal.get_history(), category)

    def open_positions(self):
        return self.engine.get_open_positions()

    def broker_status(self):
        return self.engine.orders.status()

    def risk_status(self):
        account = self.engine.account.get_account(); positions = self.open_positions()
        return {"balance": account.balance, "equity": account.equity, "drawdown_percent": account.drawdown_percent,
                "daily_profit_loss": account.daily_profit_loss, "open_positions": len(positions),
                "open_risk_percent": self.engine._total_open_risk_percent(account.balance, positions),
                "limits": {"daily_drawdown": active_config.daily_drawdown_limit, "max_drawdown": active_config.max_account_drawdown,
                           "max_open_positions": active_config.max_open_positions, "max_total_risk": active_config.max_total_risk_percent,
                           "max_consecutive_losses": active_config.max_consecutive_losses}}


__all__ = ["BotController"]

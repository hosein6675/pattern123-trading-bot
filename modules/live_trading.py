from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.account_manager import AccountManager
from modules.broker_interface import BrokerInterface, OrderResult
from modules.config import active_config
from modules.money_management import MoneyManager, PositionPlan, RiskLimits


@dataclass(frozen=True)
class LiveTradeDecision:
    approved: bool
    reason: str
    plan: PositionPlan | None = None
    result: OrderResult | None = None


class LiveTradingService:
    """Fail-closed live-trading coordinator.

    It connects only to the configured broker, synchronizes account state,
    applies money-management gates, and sends an order only after admission.
    No live market data or execution is simulated by this service.
    """

    def __init__(
        self,
        broker: BrokerInterface | None = None,
        account: AccountManager | None = None,
        money_manager: MoneyManager | None = None,
    ):
        self.broker = broker or BrokerInterface()
        self.account = account or AccountManager()
        self.money_manager = money_manager or MoneyManager(
            RiskLimits(
                risk_per_trade_percent=active_config.risk_per_trade_percent,
                daily_drawdown_limit=active_config.daily_drawdown_limit,
                max_account_drawdown=active_config.max_account_drawdown,
                max_open_positions=active_config.max_open_positions,
                max_total_risk_percent=active_config.max_total_risk_percent,
                max_consecutive_losses=active_config.max_consecutive_losses,
            )
        )

    def connect(self) -> dict[str, Any]:
        if self.broker.mode != "live":
            return {"status": "error", "mode": self.broker.mode, "message": "LiveTradingService requires TRADING_MODE=live"}
        return self.broker.connect()

    def snapshot(self) -> dict[str, Any]:
        if self.broker.mode != "live":
            return {"status": "error", "mode": self.broker.mode, "message": "Live broker is disabled"}
        account = self.broker.account_info()
        if account.get("status") not in {"ready", "connected"}:
            return {"status": "error", "mode": "live", "message": account.get("message", "Broker account unavailable")}
        self.account.sync_from_broker(account)
        return {
            "status": "ready",
            "mode": "live",
            "account": account,
            "positions": self.broker.get_positions(),
        }

    def prepare_trade(
        self,
        *,
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        current_risk_percent: float = 0.0,
        consecutive_losses: int = 0,
    ) -> LiveTradeDecision:
        if self.broker.mode != "live":
            return LiveTradeDecision(False, "Live broker is disabled")
        if not active_config.is_symbol_allowed(symbol):
            return LiveTradeDecision(False, "Symbol is not allowed")
        state = self.snapshot()
        if state.get("status") != "ready":
            return LiveTradeDecision(False, state.get("message", "Broker unavailable"))
        contract = self.broker.contract(symbol)
        if contract.get("status") != "ready":
            return LiveTradeDecision(False, contract.get("message", "Symbol contract unavailable"))
        risk_per_lot = self.broker.risk_per_lot(symbol, direction, entry, stop_loss)
        try:
            plan = self.money_manager.plan(
                direction=direction,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                equity=self.account.equity,
                peak_equity=self.account.peak_balance,
                daily_start_equity=self.account.daily_start_balance,
                risk_per_lot=risk_per_lot,
                volume_min=contract["volume_min"],
                volume_max=contract["volume_max"],
                volume_step=contract["volume_step"],
                open_positions=len(state["positions"]),
                current_risk_percent=current_risk_percent,
                consecutive_losses=consecutive_losses,
            )
        except (RuntimeError, ValueError, KeyError) as exc:
            return LiveTradeDecision(False, str(exc))
        return LiveTradeDecision(True, "Trade admitted", plan)

    def execute_trade(self, decision: LiveTradeDecision, symbol: str) -> LiveTradeDecision:
        if not decision.approved or decision.plan is None:
            return decision
        plan = decision.plan
        result = self.broker.open_order(
            symbol=symbol,
            direction=plan.direction,
            volume=plan.volume,
            stop_loss=plan.stop_loss,
            take_profit=plan.take_profit,
        )
        if not result.success:
            return LiveTradeDecision(False, result.message, plan, result)
        return LiveTradeDecision(True, result.message, plan, result)

    def close_trade(self, order_id: str) -> OrderResult:
        if self.broker.mode != "live":
            return OrderResult(False, str(order_id), "Live broker is disabled")
        return self.broker.close_order(order_id)


__all__ = ["LiveTradingService", "LiveTradeDecision"]

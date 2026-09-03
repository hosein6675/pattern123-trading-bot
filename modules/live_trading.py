from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.broker_interface import BrokerInterface, OrderResult
from modules.config import active_config
from modules.risk_manager import RiskManager, RiskResult


@dataclass(frozen=True)
class LiveTradeDecision:
    approved: bool
    reason: str
    risk: RiskResult | None = None
    result: OrderResult | None = None


class LiveTradingService:
    """Fail-closed live-trading coordinator.

    It connects only to the configured broker, synchronizes the broker account,
    applies the existing risk manager, and sends an order only after admission.
    No live market data or execution is simulated by this service.
    """

    def __init__(
        self,
        broker: BrokerInterface | None = None,
        risk_manager: RiskManager | None = None,
    ):
        self.broker = broker or BrokerInterface()
        self.risk_manager = risk_manager or RiskManager()

    def connect(self) -> dict[str, Any]:
        if self.broker.mode != "live":
            return {
                "status": "error",
                "mode": self.broker.mode,
                "message": "LiveTradingService requires TRADING_MODE=live",
            }
        return self.broker.connect()

    def snapshot(self) -> dict[str, Any]:
        if self.broker.mode != "live":
            return {"status": "error", "mode": self.broker.mode, "message": "Live broker is disabled"}
        account = self.broker.account_info()
        if account.get("status") not in {"ready", "connected"}:
            return {
                "status": "error",
                "mode": "live",
                "message": account.get("message", "Broker account unavailable"),
            }
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
        quality: float = 100.0,
        current_risk_percent: float = 0.0,
    ) -> LiveTradeDecision:
        if self.broker.mode != "live":
            return LiveTradeDecision(False, "Live broker is disabled")
        if not active_config.is_symbol_allowed(symbol):
            return LiveTradeDecision(False, "Symbol is not allowed")
        state = self.snapshot()
        if state.get("status") != "ready":
            return LiveTradeDecision(False, state.get("message", "Broker unavailable"))
        account = state["account"]
        contract = self.broker.contract(symbol)
        if contract.get("status") != "ready":
            return LiveTradeDecision(False, contract.get("message", "Symbol contract unavailable"))
        risk_per_lot = self.broker.risk_per_lot(symbol, direction, entry, stop_loss)
        risk = self.risk_manager.check(
            balance=account["balance"],
            equity=account.get("equity"),
            entry=entry,
            stop_loss=stop_loss,
            quality=quality,
            open_positions=len(state["positions"]),
            risk_per_lot=risk_per_lot,
            total_risk_percent=current_risk_percent,
            min_lot=contract["volume_min"],
            max_lot=contract["volume_max"],
            lot_step=contract["volume_step"],
        )
        if not risk.allowed:
            return LiveTradeDecision(False, risk.message, risk)
        return LiveTradeDecision(True, "Risk approved", risk)

    def execute_trade(self, decision: LiveTradeDecision, symbol: str, *, entry: float, stop_loss: float, take_profit: float) -> LiveTradeDecision:
        if not decision.approved or decision.risk is None:
            return decision
        result = self.broker.open_order(
            symbol=symbol,
            direction="buy" if take_profit > entry else "sell",
            volume=decision.risk.lot_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        if not result.success:
            return LiveTradeDecision(False, result.message, decision.risk, result)
        return LiveTradeDecision(True, result.message, decision.risk, result)

    def execute_directional_trade(
        self,
        decision: LiveTradeDecision,
        *,
        symbol: str,
        direction: str,
        stop_loss: float,
        take_profit: float,
    ) -> LiveTradeDecision:
        if not decision.approved or decision.risk is None:
            return decision
        result = self.broker.open_order(
            symbol=symbol,
            direction=direction,
            volume=decision.risk.lot_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        if not result.success:
            return LiveTradeDecision(False, result.message, decision.risk, result)
        return LiveTradeDecision(True, result.message, decision.risk, result)

    def close_trade(self, order_id: str) -> OrderResult:
        if self.broker.mode != "live":
            return OrderResult(False, str(order_id), "Live broker is disabled")
        return self.broker.close_order(order_id)


__all__ = ["LiveTradingService", "LiveTradeDecision"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.live_trading import LiveTradeDecision, LiveTradingService


@dataclass(frozen=True, slots=True)
class BrokerStationState:
    """Operator-facing state of the live broker boundary."""

    mode: str
    connected: bool
    armed: bool
    account: dict[str, Any]
    positions: list[dict[str, Any]]
    message: str = ""


class LiveBrokerStation:
    """Safe live-broker station around the existing MT5/live-trading boundary.

    Connection and execution are separate states. A connected broker is never
    considered permission to trade; an operator must explicitly arm execution.
    """

    def __init__(self, service: LiveTradingService | None = None):
        self.service = service or LiveTradingService()
        self._armed = False

    @property
    def armed(self) -> bool:
        return self._armed

    def arm(self) -> bool:
        if self.service.broker.mode != "live":
            self._armed = False
            return False
        self._armed = True
        return True

    def disarm(self) -> None:
        self._armed = False

    def connect(self) -> dict[str, Any]:
        result = self.service.connect()
        if result.get("status") != "connected":
            self._armed = False
        return result

    def state(self) -> BrokerStationState:
        snapshot = self.service.snapshot()
        if snapshot.get("status") != "ready":
            return BrokerStationState(
                mode=self.service.broker.mode,
                connected=False,
                armed=False,
                account={},
                positions=[],
                message=snapshot.get("message", "Broker unavailable"),
            )
        return BrokerStationState(
            mode="live",
            connected=True,
            armed=self._armed,
            account=snapshot.get("account", {}),
            positions=snapshot.get("positions", []),
            message="Broker connected; execution remains disarmed" if not self._armed else "Broker connected and execution armed",
        )

    def prepare_trade(self, **kwargs: Any) -> LiveTradeDecision:
        return self.service.prepare_trade(**kwargs)

    def execute(self, decision: LiveTradeDecision, *, symbol: str, direction: str, stop_loss: float, take_profit: float) -> LiveTradeDecision:
        if not self._armed:
            return LiveTradeDecision(False, "Live broker station is disarmed", decision.risk)
        return self.service.execute_directional_trade(
            decision,
            symbol=symbol,
            direction=direction,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close(self, order_id: str):
        if not self._armed:
            from modules.broker_interface import OrderResult

            return OrderResult(False, str(order_id), "Live broker station is disarmed")
        return self.service.close_trade(order_id)


__all__ = ["BrokerStationState", "LiveBrokerStation"]

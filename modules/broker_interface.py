from __future__ import annotations

from dataclasses import dataclass

from modules.config import active_config


@dataclass(frozen=True)
class OrderResult:
    success: bool
    order_id: str
    message: str


class DemoBroker:
    """Deterministic broker used only when TRADING_MODE=demo."""

    def connect(self) -> dict[str, str]:
        return {"status": "connected", "mode": "demo"}

    def open_order(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: float,
    ) -> OrderResult:
        return OrderResult(
            success=True,
            order_id="DEMO_ORDER",
            message="Order created in demo mode",
        )

    def close_order(self, order_id: str) -> OrderResult:
        return OrderResult(
            success=True,
            order_id=str(order_id),
            message="Order closed in demo mode",
        )

    def get_positions(self) -> list[object]:
        return []

    def account_info(self) -> dict[str, object]:
        return {
            "status": "ready",
            "mode": "demo",
            "balance": 1000.0,
            "equity": 1000.0,
            "currency": "USD",
        }

    def risk_per_lot(self, symbol: str, direction: str, entry: float, stop_loss: float) -> float:
        distance = abs(float(entry) - float(stop_loss))
        return distance if distance > 0 else 0.0


class BrokerInterface:
    """Broker facade with fail-closed live/demonstration separation."""

    def __init__(self) -> None:
        if active_config.mode == "live":
            from modules.mt5_broker import MT5Broker

            self.broker = MT5Broker()
        else:
            self.broker = DemoBroker()

    @property
    def mode(self) -> str:
        return active_config.mode

    def connect(self) -> dict[str, object]:
        return self.broker.connect()

    def disconnect(self) -> None:
        disconnect = getattr(self.broker, "disconnect", None)
        if disconnect is not None:
            disconnect()

    def open_order(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: float,
    ) -> OrderResult:
        return self.broker.open_order(
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close_order(self, order_id: str) -> OrderResult:
        return self.broker.close_order(order_id)

    def get_positions(self) -> list[object]:
        return self.broker.get_positions()

    def account_info(self) -> dict[str, object]:
        method = getattr(self.broker, "account_info", None)
        if method is None:
            return {"status": "unavailable", "mode": self.mode}
        return method()

    def risk_per_lot(
        self,
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
    ) -> float:
        method = getattr(self.broker, "risk_per_lot", None)
        if method is None:
            return 0.0
        return float(method(symbol, direction, entry, stop_loss))

    def status(self) -> dict[str, object]:
        connection = self.connect()
        return {
            "mode": self.mode,
            "status": connection.get("status", "unknown"),
            "message": connection.get("message", ""),
        }

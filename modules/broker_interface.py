from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderResult:
    success: bool
    order_id: str
    message: str


class BrokerInterface:
    """Safe demo broker contract used until a real MT5 adapter is configured."""

    def __init__(self) -> None:
        self.connection = "demo"

    def connect(self) -> dict[str, str]:
        return {"status": "connected", "mode": self.connection}

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
            message="Order closed",
        )

    def get_positions(self) -> list[object]:
        return []

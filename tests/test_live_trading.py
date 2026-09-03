from dataclasses import dataclass

from modules.broker_interface import OrderResult
from modules.live_trading import LiveTradingService
from modules.risk_manager import RiskManager


@dataclass
class FakeLiveBroker:
    mode: str = "live"
    orders: list[dict] | None = None

    def __post_init__(self):
        self.orders = []

    def connect(self):
        return {"status": "connected", "mode": "live"}

    def account_info(self):
        return {"status": "ready", "mode": "live", "balance": 1000.0, "equity": 1000.0}

    def get_positions(self):
        return []

    def contract(self, symbol):
        return {"status": "ready", "symbol": symbol, "volume_min": 0.01, "volume_max": 10.0, "volume_step": 0.01}

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        return 100.0

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        self.orders.append({"symbol": symbol, "direction": direction, "volume": volume, "sl": stop_loss, "tp": take_profit})
        return OrderResult(True, "LIVE-1", "Live order executed")

    def close_order(self, order_id):
        return OrderResult(True, str(order_id), "Live position closed")


def test_live_service_requires_live_mode():
    class DemoLike:
        mode = "demo"

    service = LiveTradingService(broker=DemoLike(), risk_manager=RiskManager())
    result = service.connect()
    assert result["status"] == "error"
    assert "requires TRADING_MODE=live" in result["message"]


def test_live_service_sizes_and_executes_only_after_risk_approval():
    broker = FakeLiveBroker()
    service = LiveTradingService(broker=broker, risk_manager=RiskManager())

    decision = service.prepare_trade(
        symbol="EURUSD",
        direction="buy",
        entry=1.1000,
        stop_loss=1.0900,
        take_profit=1.1200,
        quality=95,
    )

    assert decision.approved is True
    assert decision.risk is not None
    assert decision.risk.lot_size == 0.1

    executed = service.execute_directional_trade(
        decision,
        symbol="EURUSD",
        direction="buy",
        stop_loss=1.0900,
        take_profit=1.1200,
    )
    assert executed.approved is True
    assert executed.result is not None
    assert broker.orders[0]["volume"] == 0.1


def test_live_service_rejects_disallowed_symbol_before_order():
    broker = FakeLiveBroker()
    service = LiveTradingService(broker=broker, risk_manager=RiskManager())
    result = service.prepare_trade(
        symbol="NOT_ALLOWED",
        direction="buy",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
    )
    assert result.approved is False
    assert result.reason == "Symbol is not allowed"
    assert broker.orders == []

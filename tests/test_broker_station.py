from modules.broker_interface import OrderResult
from modules.broker_station import LiveBrokerStation
from modules.live_trading import LiveTradeDecision, LiveTradingService
from modules.risk_manager import RiskManager


class FakeLiveBroker:
    mode = "live"

    def __init__(self):
        self.opened = []

    def connect(self):
        return {"status": "connected", "mode": "live"}

    def account_info(self):
        return {"status": "ready", "mode": "live", "balance": 1000.0, "equity": 1000.0}

    def get_positions(self):
        return []

    def contract(self, symbol):
        return {
            "status": "ready",
            "symbol": symbol,
            "volume_min": 0.01,
            "volume_max": 10.0,
            "volume_step": 0.01,
        }

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        return 100.0

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        self.opened.append((symbol, direction, volume, stop_loss, take_profit))
        return OrderResult(True, "T1", "executed")

    def close_order(self, order_id):
        return OrderResult(True, str(order_id), "closed")


def make_station():
    broker = FakeLiveBroker()
    service = LiveTradingService(broker=broker, risk_manager=RiskManager())
    return LiveBrokerStation(service), broker


def test_station_starts_disarmed_and_refuses_execution():
    station, broker = make_station()
    decision = LiveTradeDecision(True, "Risk approved")

    result = station.execute(
        decision,
        symbol="EURUSD",
        direction="buy",
        stop_loss=1.09,
        take_profit=1.13,
    )

    assert result.approved is False
    assert result.reason == "Live broker station is disarmed"
    assert broker.opened == []


def test_station_requires_explicit_arm_before_live_execution():
    station, broker = make_station()
    station.connect()
    assert station.arm() is True

    decision = station.prepare_trade(
        symbol="EURUSD",
        direction="buy",
        entry=1.10,
        stop_loss=1.09,
        take_profit=1.13,
        quality=95,
    )
    result = station.execute(
        decision,
        symbol="EURUSD",
        direction="buy",
        stop_loss=1.09,
        take_profit=1.13,
    )

    assert result.approved is True
    assert broker.opened == [("EURUSD", "buy", 0.1, 1.09, 1.13)]


def test_disarm_blocks_close_as_well():
    station, _ = make_station()
    result = station.close("T1")
    assert result.success is False
    assert result.message == "Live broker station is disarmed"

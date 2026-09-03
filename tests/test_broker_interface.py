from modules.broker_interface import BrokerInterface


def test_demo_broker_is_safe_and_deterministic():
    broker = BrokerInterface()

    assert broker.mode == "demo"
    assert broker.status()["status"] == "connected"

    account = broker.account_info()
    assert account["status"] == "ready"
    assert account["balance"] == 1000.0

    order = broker.open_order("EURUSD", "buy", 0.01, 1.09, 1.13)
    assert order.success is True
    assert order.order_id == "DEMO_ORDER"

    assert broker.current_price("EURUSD")["ask"] == 1.1
    assert broker.contract("EURUSD")["volume_step"] == 0.01

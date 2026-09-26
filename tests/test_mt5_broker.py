from types import SimpleNamespace

from modules.mt5_broker import MT5Broker, MT5Settings


class FakeMT5:
    def __init__(self, connected=True, account=True):
        self.connected = connected
        self.account = account
        self.selected = False

    def initialize(self, **kwargs):
        return True

    def terminal_info(self):
        return SimpleNamespace(connected=self.connected)

    def account_info(self):
        return SimpleNamespace(login=123, server="demo") if self.account else None

    def last_error(self):
        return (1, "fake error")

    def shutdown(self):
        pass

    def symbol_info(self, symbol):
        if self.selected:
            return SimpleNamespace(
                visible=True,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                trade_tick_size=0.01,
                trade_tick_value=1.0,
                digits=2,
            )
        return SimpleNamespace(
            visible=False,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            digits=2,
        )

    def symbol_select(self, symbol, enable):
        self.selected = bool(enable)
        return self.selected


def _broker(fake):
    broker = MT5Broker(MT5Settings())
    broker._mt5 = fake
    return broker


def test_connect_requires_connected_mt5_terminal():
    broker = _broker(FakeMT5(connected=False))
    result = broker.connect()
    assert result["status"] == "error"
    assert "not connected" in result["message"].lower()
    assert broker._connected is False


def test_connect_requires_account_info():
    broker = _broker(FakeMT5(connected=True, account=False))
    result = broker.connect()
    assert result["status"] == "error"
    assert broker._connected is False


def test_symbol_info_rechecks_visibility_after_selection():
    fake = FakeMT5()
    broker = _broker(fake)
    broker._connected = True
    result = broker.symbol_info("XAUUSD")
    assert result["status"] == "ready"
    assert result["visible"] is True
    assert fake.selected is True

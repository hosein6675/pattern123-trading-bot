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

    def connect(self):
        return {"status": "connected", "mode": "demo"}

    def disconnect(self):
        return None

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        return OrderResult(True, "DEMO_ORDER", "Order created in demo mode")

    def close_order(self, order_id):
        return OrderResult(True, str(order_id), "Order closed in demo mode")

    def get_positions(self):
        return []

    def account_info(self):
        return {"status": "ready", "mode": "demo", "balance": 1000.0, "equity": 1000.0, "currency": "USD"}

    def current_price(self, symbol):
        prices = {"EURUSD": 1.1, "GBPUSD": 1.3, "USDJPY": 150.0, "XAUUSD": 2400.0, "BTCUSD": 60000.0}
        price = prices.get(symbol, 100.0)
        return {"status": "ready", "symbol": symbol, "bid": price, "ask": price}

    def contract(self, symbol):
        return {"status": "ready", "symbol": symbol, "volume_min": active_config.min_lot, "volume_max": active_config.max_lot, "volume_step": active_config.lot_step}

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        distance = abs(float(entry) - float(stop_loss))
        return distance if distance > 0 else 0.0


class DisabledLiveBroker:
    """Fail-closed broker used until an operator explicitly enables live trading."""

    def _error(self, message="Live trading is disabled"):
        return {"status": "disabled", "mode": "live", "message": message}

    def connect(self):
        return self._error()

    def disconnect(self):
        return None

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        return OrderResult(False, "", "Live trading is disabled")

    def close_order(self, order_id):
        return OrderResult(False, str(order_id), "Live trading is disabled")

    def get_positions(self):
        return []

    def account_info(self):
        return self._error()

    def current_price(self, symbol):
        return {**self._error(), "symbol": symbol}

    def get_candles(self, symbol, timeframe, count=200):
        return {**self._error(), "candles": [], "symbol": symbol, "timeframe": timeframe}

    def contract(self, symbol):
        return {**self._error(), "symbol": symbol}

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        return 0.0


class BrokerInterface:
    """Broker facade with fail-closed live/demonstration separation."""

    def __init__(self):
        if active_config.mode == "live" and active_config.live_trading_enabled:
            from modules.mt5_broker import MT5Broker
            self.broker = MT5Broker()
        elif active_config.mode == "live":
            self.broker = DisabledLiveBroker()
        else:
            self.broker = DemoBroker()

    @property
    def mode(self):
        return active_config.mode

    def connect(self):
        return self.broker.connect()

    def disconnect(self):
        self.broker.disconnect()

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        return self.broker.open_order(symbol, direction, volume, stop_loss, take_profit)

    def close_order(self, order_id):
        return self.broker.close_order(order_id)

    def get_positions(self):
        return self.broker.get_positions()

    def account_info(self):
        method = getattr(self.broker, "account_info", None)
        return method() if method else {"status": "unavailable", "mode": self.mode}

    def current_price(self, symbol):
        method = getattr(self.broker, "current_price", None)
        return method(symbol) if method else {"status": "unavailable", "symbol": symbol}

    def get_candles(self, symbol, timeframe, count=200):
        method = getattr(self.broker, "get_candles", None)
        if method is None:
            return {"status": "unavailable", "candles": [], "message": "Broker has no live market-data adapter"}
        return method(symbol, timeframe, count)

    def contract(self, symbol):
        method = getattr(self.broker, "symbol_info", None) or getattr(self.broker, "contract", None)
        return method(symbol) if method else {"status": "unavailable", "symbol": symbol}

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        method = getattr(self.broker, "risk_per_lot", None)
        return float(method(symbol, direction, entry, stop_loss)) if method else 0.0

    def status(self):
        connection = self.connect()
        return {"mode": self.mode, "status": connection.get("status", "unknown"), "message": connection.get("message", "")}

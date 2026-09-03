from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from modules.broker_interface import OrderResult


@dataclass(frozen=True)
class MT5Settings:
    """Connection settings read from environment; credentials never live in code."""

    login: int | None = None
    password: str | None = None
    server: str | None = None
    terminal_path: str | None = None

    @classmethod
    def from_env(cls):
        raw_login = os.getenv("MT5_LOGIN", "").strip()
        return cls(
            login=int(raw_login) if raw_login.isdigit() else None,
            password=os.getenv("MT5_PASSWORD") or None,
            server=os.getenv("MT5_SERVER") or None,
            terminal_path=os.getenv("MT5_TERMINAL_PATH") or None,
        )


class MT5Broker:
    """Thin, fail-closed MetaTrader 5 adapter.

    MetaTrader5 is loaded lazily, so demo/backtest CI needs no terminal SDK.
    Live execution is never simulated: SDK/terminal errors become failures.
    """

    def __init__(self, settings=None):
        self.settings = settings or MT5Settings.from_env()
        self._mt5: Any = None
        self._connected = False

    def _load(self):
        if self._mt5 is not None:
            return self._mt5
        try:
            import MetaTrader5 as mt5  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("MetaTrader5 package is not installed; live trading is unavailable") from exc
        self._mt5 = mt5
        return mt5

    def connect(self):
        try:
            mt5 = self._load()
            kwargs = {}
            if self.settings.login is not None:
                kwargs["login"] = self.settings.login
            if self.settings.password is not None:
                kwargs["password"] = self.settings.password
            if self.settings.server is not None:
                kwargs["server"] = self.settings.server
            ok = mt5.initialize(self.settings.terminal_path, **kwargs) if self.settings.terminal_path else mt5.initialize(**kwargs)
            if not ok:
                return {"status": "error", "mode": "live", "message": str(mt5.last_error())}
            self._connected = True
            account = mt5.account_info()
            return {"status": "connected", "mode": "live", "login": getattr(account, "login", None), "server": getattr(account, "server", None)}
        except Exception as exc:
            self._connected = False
            return {"status": "error", "mode": "live", "message": str(exc)}

    def disconnect(self):
        if self._mt5 is not None:
            self._mt5.shutdown()
        self._connected = False

    def _ensure_connected(self):
        if self._connected:
            return True
        return self.connect().get("status") == "connected"

    def account_info(self):
        if not self._ensure_connected():
            return {"status": "error", "mode": "live", "message": "MT5 connection unavailable"}
        account = self._mt5.account_info()
        if account is None:
            return {"status": "error", "message": str(self._mt5.last_error())}
        return {
            "status": "ready",
            "mode": "live",
            "login": getattr(account, "login", None),
            "balance": float(getattr(account, "balance", 0.0)),
            "equity": float(getattr(account, "equity", 0.0)),
            "margin": float(getattr(account, "margin", 0.0)),
            "free_margin": float(getattr(account, "margin_free", 0.0)),
            "currency": getattr(account, "currency", ""),
        }

    def symbol_info(self, symbol):
        if not self._ensure_connected():
            return {"status": "error", "symbol": symbol, "message": "MT5 connection unavailable"}
        info = self._mt5.symbol_info(symbol)
        if info is None:
            return {"status": "error", "symbol": symbol, "message": str(self._mt5.last_error())}
        if not getattr(info, "visible", False):
            self._mt5.symbol_select(symbol, True)
        return {
            "status": "ready",
            "symbol": symbol,
            "visible": bool(getattr(info, "visible", False)),
            "volume_min": float(getattr(info, "volume_min", 0.0)),
            "volume_max": float(getattr(info, "volume_max", 0.0)),
            "volume_step": float(getattr(info, "volume_step", 0.0)),
            "trade_tick_size": float(getattr(info, "trade_tick_size", 0.0)),
            "trade_tick_value": float(getattr(info, "trade_tick_value", 0.0)),
            "digits": int(getattr(info, "digits", 0)),
        }

    def current_price(self, symbol):
        if not self._ensure_connected():
            return {"status": "error", "symbol": symbol, "message": "MT5 connection unavailable"}
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"status": "error", "symbol": symbol, "message": str(self._mt5.last_error())}
        return {"status": "ready", "symbol": symbol, "bid": float(tick.bid), "ask": float(tick.ask), "time": int(tick.time)}

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        if not self._ensure_connected():
            return 0.0
        order_type = self._mt5.ORDER_TYPE_BUY if direction == "buy" else self._mt5.ORDER_TYPE_SELL
        pnl = self._mt5.order_calc_profit(order_type, symbol, 1.0, float(entry), float(stop_loss))
        return abs(float(pnl)) if pnl is not None else 0.0

    def open_order(self, symbol, direction, volume, stop_loss, take_profit):
        if not self._ensure_connected():
            return OrderResult(False, "", "MT5 connection unavailable")
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return OrderResult(False, "", str(self._mt5.last_error()))
        order_type = self._mt5.ORDER_TYPE_BUY if direction == "buy" else self._mt5.ORDER_TYPE_SELL
        price = float(tick.ask if direction == "buy" else tick.bid)
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": float(stop_loss),
            "tp": float(take_profit),
            "deviation": int(os.getenv("MT5_DEVIATION", "20")),
            "magic": int(os.getenv("MT5_MAGIC", "123123")),
            "comment": "pattern123",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_IOC,
        }
        result = self._mt5.order_send(request)
        if result is None:
            return OrderResult(False, "", str(self._mt5.last_error()))
        if result.retcode != self._mt5.TRADE_RETCODE_DONE:
            return OrderResult(False, str(getattr(result, "order", "")), f"MT5 retcode {result.retcode}")
        return OrderResult(True, str(getattr(result, "order", "")), "Live order executed")

    def close_order(self, order_id):
        if not self._ensure_connected():
            return OrderResult(False, str(order_id), "MT5 connection unavailable")
        try:
            ticket = int(order_id)
        except (TypeError, ValueError):
            return OrderResult(False, str(order_id), "Invalid MT5 ticket")
        positions = self._mt5.positions_get(ticket=ticket)
        if not positions:
            return OrderResult(False, str(order_id), "Position not found")
        pos = positions[0]
        tick = self._mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return OrderResult(False, str(order_id), str(self._mt5.last_error()))
        close_type = self._mt5.ORDER_TYPE_SELL if pos.type == self._mt5.POSITION_TYPE_BUY else self._mt5.ORDER_TYPE_BUY
        price = float(tick.bid if pos.type == self._mt5.POSITION_TYPE_BUY else tick.ask)
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": float(pos.volume),
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": int(os.getenv("MT5_DEVIATION", "20")),
            "magic": int(os.getenv("MT5_MAGIC", "123123")),
            "comment": "pattern123-close",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_IOC,
        }
        result = self._mt5.order_send(request)
        if result is None:
            return OrderResult(False, str(order_id), str(self._mt5.last_error()))
        if result.retcode != self._mt5.TRADE_RETCODE_DONE:
            return OrderResult(False, str(order_id), f"MT5 retcode {result.retcode}")
        return OrderResult(True, str(order_id), "Live position closed")

    def get_positions(self):
        if not self._ensure_connected():
            return []
        positions = self._mt5.positions_get() or []
        return [
            {
                "ticket": int(pos.ticket),
                "symbol": pos.symbol,
                "direction": "buy" if pos.type == self._mt5.POSITION_TYPE_BUY else "sell",
                "volume": float(pos.volume),
                "price_open": float(pos.price_open),
                "sl": float(pos.sl),
                "tp": float(pos.tp),
                "profit": float(pos.profit),
            }
            for pos in positions
        ]

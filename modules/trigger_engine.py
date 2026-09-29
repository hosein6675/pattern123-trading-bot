from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class TriggerResult:
    status: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confirmations: dict[str, bool]
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    message: str = ""


class TriggerEngine:
    """Final pre-execution gate; it never creates market data or prices."""

    def evaluate(self, strategy, price_action, macd, trendline_fan, candles=None):
        if strategy is None or price_action is None or macd is None:
            return self._no_trade("Required trigger input unavailable")

        direction = str(getattr(strategy, "direction", "none")).lower()
        entry = self._finite(getattr(strategy, "entry", 0))
        stop = self._finite(getattr(strategy, "stop_loss", 0))
        target = self._finite(getattr(strategy, "tp3", 0) or getattr(strategy, "tp2", 0) or getattr(strategy, "tp1", 0))
        rr = self._finite(getattr(strategy, "risk_reward", 0))

        confirmations = {
            "strategy_approved": bool(getattr(strategy, "approved", False)),
            "candle_confirmation": bool(getattr(price_action, "engulfing", False)),
            "momentum_confirmation": bool(getattr(macd, "momentum_confirmation", False)),
            "trendline_confirmation": self._trendline_confirmed(trendline_fan, direction),
            "risk_reward": rr > 0,
        }

        reasons = []
        warnings = []
        for name, passed in confirmations.items():
            if passed:
                reasons.append(name)
            else:
                warnings.append(f"{name} missing")

        if not confirmations["strategy_approved"]:
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Strategy gate rejected setup")
        if direction not in {"buy", "sell"}:
            return self._result("NO_TRADE", "none", entry, stop, target, rr, confirmations, reasons, warnings,
                                "Trigger direction unavailable")
        if not confirmations["candle_confirmation"]:
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Candle confirmation missing")
        if not confirmations["momentum_confirmation"]:
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Momentum confirmation missing")
        if not confirmations["trendline_confirmation"]:
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Trendline confirmation missing")
        if not confirmations["risk_reward"] or rr <= 0:
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Risk/reward is unavailable")

        if not self._valid_levels(direction, entry, stop, target):
            return self._result("NO_TRADE", direction, entry, stop, target, rr, confirmations, reasons, warnings,
                                "Invalid entry/SL/TP levels")

        volume_status = self._volume_status(candles)
        if volume_status is not True:
            warnings.append("Volume confirmation missing")
        else:
            reasons.append("volume_confirmation")

        # Volume is reported when MT5 supplies usable volume, but is not silently
        # treated as confirmed when the broker/feed does not provide it.
        return self._result(
            "READY", direction, entry, stop, target, rr, confirmations, reasons, warnings,
            "Trigger conditions satisfied",
        )

    @staticmethod
    def _trendline_confirmed(fan, direction):
        if fan is None:
            return False
        try:
            score = int(getattr(fan, "score", 0))
        except (TypeError, ValueError):
            score = 0
        return score > 0 and str(getattr(fan, "direction", "none")).lower() == direction

    @staticmethod
    def _volume_status(candles):
        if not candles or len(candles) < 2:
            return None
        try:
            current = float(candles[-1].get("volume", candles[-1].get("tick_volume", 0)))
            previous = float(candles[-2].get("volume", candles[-2].get("tick_volume", 0)))
        except (AttributeError, TypeError, ValueError):
            return None
        if not isfinite(current) or not isfinite(previous) or previous <= 0:
            return None
        return current >= previous

    @staticmethod
    def _valid_levels(direction, entry, stop, target):
        if min(entry, stop, target) <= 0:
            return False
        if direction == "buy":
            return stop < entry < target
        if direction == "sell":
            return target < entry < stop
        return False

    @staticmethod
    def _finite(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        return number if isfinite(number) else 0.0

    @staticmethod
    def _result(status, direction, entry, stop, target, rr, confirmations, reasons, warnings, message):
        return TriggerResult(
            status=status,
            direction=direction,
            entry=entry,
            stop_loss=stop,
            take_profit=target,
            risk_reward=rr,
            confirmations=dict(confirmations),
            reasons=list(reasons),
            warnings=list(warnings),
            message=message,
        )

    def _no_trade(self, message):
        return self._result(
            "NO_TRADE", "none", 0.0, 0.0, 0.0, 0.0,
            {}, [], [message], message,
        )

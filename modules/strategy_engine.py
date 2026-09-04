from dataclasses import dataclass, field
from math import isfinite

from modules.strategy_config import active_strategy


@dataclass(frozen=True)
class StrategyResult:
    approved: bool
    score: int
    confidence: int
    direction: str
    entry: float = 0.0
    stop_loss: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    risk_reward: float = 0.0
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    message: str = ""


class StrategyEngine:
    """Deterministic, direction-aware Pattern123 strategy decision gate."""

    def __init__(self, config=None):
        self.config = config or active_strategy

    def evaluate(self, structure, price_action, macd, market_context, trendline_fan=None, timeframe=None):
        reasons, warnings = [], []
        score = 0
        if any(item is None for item in (structure, price_action, macd, market_context)):
            return self.no_trade("Required strategy input unavailable")
        normalized_timeframe = str(timeframe).upper() if timeframe is not None else None
        if normalized_timeframe and normalized_timeframe not in self.config.allowed_timeframes:
            return self.no_trade("Timeframe not allowed")

        structure_trend = str(getattr(structure, "trend", "unknown")).lower()
        pa_direction = str(getattr(price_action, "direction", "none")).lower()
        pattern_valid = bool(getattr(price_action, "pattern_valid", False))
        pa_confidence = self._bounded_int(getattr(price_action, "confidence", 0))
        structure_quality = self._bounded_int(getattr(structure, "structure_quality", 0))

        if self.config.require_structure:
            if structure_trend in {"bullish", "bearish"} and structure_quality >= self.config.minimum_structure_quality:
                score += 25
                reasons.append("Market structure confirmed")
            else:
                return self._result(False, score, score, "none", price_action, reasons,
                                    ["Market structure not confirmed"], "Required market structure confirmation missing")

        if self.config.require_pattern_confirmation:
            if pattern_valid and pa_confidence >= self.config.minimum_price_action_confidence:
                score += 30
                reasons.append("Pattern123 price action confirmed")
            else:
                return self._result(False, score, score, "none", price_action, reasons,
                                    ["Pattern123 confirmation below threshold"], "Required Pattern123 confirmation missing")

        engulfing = bool(getattr(price_action, "engulfing", False))
        if self.config.require_engulfing and not engulfing:
            return self._result(False, score, score, "none", price_action, reasons,
                                ["Engulfing confirmation missing"],
                                "Required engulfing confirmation missing")
        if engulfing:
            reasons.append("Engulfing confirmed")

        direction = self._direction(structure_trend, pa_direction)
        if direction == "none":
            return self._result(False, score, score, "none", price_action, reasons,
                                warnings + ["Structure and Pattern123 direction mismatch"],
                                "Structure and Pattern123 direction mismatch")

        if self.config.use_macd_filter:
            macd_score = self._bounded_int(getattr(macd, "score", 0))
            macd_direction = self._macd_direction(macd)
            if macd_score < self.config.minimum_macd_score:
                warnings.append("MACD confirmation below directional threshold")
                return self._result(False, score, score, direction, price_action, reasons, warnings,
                                    "MACD filter rejected setup")
            if macd_direction != direction:
                warnings.append("MACD direction conflicts with trade direction")
                return self._result(False, score, score, direction, price_action, reasons, warnings,
                                    "MACD direction conflict")
            score += 20
            reasons.append("MACD confirms trade direction")
            if self.config.require_macd_momentum:
                if bool(getattr(macd, "momentum_confirmation", False)):
                    score += 10
                    reasons.append("MACD momentum confirms direction")
                else:
                    return self._result(False, score, score, direction, price_action, reasons,
                                        warnings + ["MACD momentum does not confirm direction"],
                                        "MACD momentum confirmation missing")

        context_confidence = self._bounded_int(getattr(market_context, "confidence", 0))
        context_trend = str(getattr(market_context, "trend", "unknown")).lower()
        if context_confidence >= 70 and context_trend == structure_trend:
            score += 10
            reasons.append("Multi-timeframe context aligned")
        else:
            warnings.append("Market context not aligned")

        if self.config.require_trendline_fan:
            fan_score = self._bounded_int(getattr(trendline_fan, "score", 0)) if trendline_fan else 0
            fan_direction = str(getattr(trendline_fan, "direction", "none")).lower() if trendline_fan else "none"
            if fan_score < self.config.minimum_trendline_score or fan_direction != direction:
                return self._result(False, score, score, direction, price_action, reasons,
                                    warnings + ["Trendline fan does not confirm direction"],
                                    "Trendline fan confirmation missing")
            score += 5
            reasons.append("Trendline fan confirms direction")

        entry = self._finite_float(getattr(price_action, "entry", 0.0))
        stop_loss = self._finite_float(getattr(price_action, "stop_loss", 0.0))
        tp1 = self._finite_float(getattr(price_action, "tp1", 0.0))
        tp2 = self._finite_float(getattr(price_action, "tp2", 0.0))
        tp3 = self._finite_float(getattr(price_action, "tp3", 0.0))
        risk_reward = self._risk_reward(direction, entry, stop_loss, tp3 or tp2 or tp1)
        if direction != "none" and risk_reward >= self.config.risk_reward_ratio:
            reasons.append(f"Risk/reward target >= {self.config.risk_reward_ratio:g}")
        elif direction != "none":
            return self._result(False, score, score, direction, price_action, reasons,
                                warnings + ["Risk/reward below configured target"],
                                "Insufficient risk/reward")

        confidence = min(100, score + (5 if pa_confidence >= 80 else 0))
        approved = score >= self.config.minimum_trade_quality and confidence >= self.config.minimum_trade_confidence
        return self._result(
            approved, score, confidence, direction, price_action, reasons, warnings,
            "Strategy conditions satisfied" if approved else "Strategy conditions failed",
            entry=entry, stop_loss=stop_loss, tp1=tp1, tp2=tp2, tp3=tp3, risk_reward=risk_reward,
        )

    @staticmethod
    def _direction(structure_trend, pa_direction):
        if structure_trend == "bullish" and pa_direction == "buy":
            return "buy"
        if structure_trend == "bearish" and pa_direction == "sell":
            return "sell"
        return "none"

    @staticmethod
    def _macd_direction(macd):
        trend = bool(getattr(macd, "trend_confirmation", False))
        histogram = float(getattr(macd, "histogram", 0.0) or 0.0)
        if trend and histogram > 0:
            return "buy"
        if not trend and histogram < 0:
            return "sell"
        return "none"

    @staticmethod
    def _risk_reward(direction, entry, stop_loss, target):
        if direction == "buy" and entry > stop_loss > 0 and target > entry:
            return round((target - entry) / (entry - stop_loss), 4)
        if direction == "sell" and stop_loss > entry > 0 and 0 < target < entry:
            return round((entry - target) / (stop_loss - entry), 4)
        return 0.0

    @staticmethod
    def _finite_float(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        return number if isfinite(number) else 0.0

    @staticmethod
    def _bounded_int(value):
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return 0

    def _result(self, approved, score, confidence, direction, price_action, reasons, warnings, message,
                entry=None, stop_loss=None, tp1=None, tp2=None, tp3=None, risk_reward=None):
        return StrategyResult(
            approved=bool(approved),
            score=max(0, min(100, int(score))),
            confidence=max(0, min(100, int(confidence))),
            direction=direction,
            entry=self._finite_float(getattr(price_action, "entry", 0.0) if entry is None else entry),
            stop_loss=self._finite_float(getattr(price_action, "stop_loss", 0.0) if stop_loss is None else stop_loss),
            tp1=self._finite_float(getattr(price_action, "tp1", 0.0) if tp1 is None else tp1),
            tp2=self._finite_float(getattr(price_action, "tp2", 0.0) if tp2 is None else tp2),
            tp3=self._finite_float(getattr(price_action, "tp3", 0.0) if tp3 is None else tp3),
            risk_reward=self._finite_float(0.0 if risk_reward is None else risk_reward),
            reasons=list(reasons),
            warnings=list(warnings),
            message=message,
        )

    def no_trade(self, message):
        return self._result(False, 0, 0, "none", None, [], [message], message)

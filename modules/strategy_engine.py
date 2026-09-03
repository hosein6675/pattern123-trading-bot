from dataclasses import dataclass, field

from modules.strategy_config import active_strategy


@dataclass
class StrategyResult:
    approved: bool
    score: int
    confidence: int
    direction: str
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    message: str = ""


class StrategyEngine:
    """Final deterministic Pattern123 strategy gate."""

    def __init__(self):
        self.config = active_strategy

    def evaluate(self, structure, price_action, macd, market_context, trendline_fan=None, timeframe=None):
        reasons, warnings, score = [], [], 0
        if any(item is None for item in (structure, price_action, macd, market_context)):
            return self.no_trade("Required strategy input unavailable")
        if timeframe is not None and timeframe not in self.config.allowed_timeframes:
            return self.no_trade("Timeframe not allowed")

        structure_trend = getattr(structure, "trend", "unknown")
        pa_direction = getattr(price_action, "direction", "none")
        if self.config.require_structure:
            quality = int(getattr(structure, "structure_quality", 0) or 0)
            if structure_trend in ("bullish", "bearish") and quality >= self.config.minimum_structure_quality:
                score += 25; reasons.append("Market structure confirmed")
            else:
                warnings.append("Market structure not confirmed")

        pattern_valid = bool(getattr(price_action, "pattern_valid", False))
        pa_confidence = int(getattr(price_action, "confidence", 0) or 0)
        if self.config.require_pattern_confirmation and pattern_valid and pa_confidence >= self.config.minimum_price_action_confidence:
            score += 30; reasons.append("Pattern123 price action confirmed")
        else:
            warnings.append("Pattern123 confirmation below threshold")

        if self.config.require_engulfing and not getattr(price_action, "engulfing", False):
            return self._result(False, score, score, "none", reasons, warnings + ["Engulfing confirmation missing"], "Required engulfing confirmation missing")
        if getattr(price_action, "engulfing", False):
            reasons.append("Engulfing confirmed")

        if self.config.use_macd_filter:
            macd_score = int(getattr(macd, "score", 0) or 0)
            if macd_score >= self.config.minimum_macd_score:
                score += 20; reasons.append("MACD confirmation accepted")
            else:
                warnings.append("MACD score weak")
            if self.config.require_macd_momentum:
                if getattr(macd, "momentum_confirmation", False):
                    score += 10; reasons.append("MACD momentum confirmed")
                else:
                    warnings.append("MACD momentum missing")

        context_confidence = int(getattr(market_context, "confidence", 0) or 0)
        context_trend = getattr(market_context, "trend", "unknown")
        if context_confidence >= 70 and context_trend == structure_trend:
            score += 10; reasons.append("Multi-timeframe context aligned")
        else:
            warnings.append("Market context not aligned")

        if self.config.require_trendline_fan:
            fan_score = int(getattr(trendline_fan, "score", 0) or 0) if trendline_fan else 0
            fan_direction = getattr(trendline_fan, "direction", "none") if trendline_fan else "none"
            if fan_score >= self.config.minimum_trendline_score and fan_direction == pa_direction:
                score += 5; reasons.append("Trendline fan confirms direction")
            else:
                warnings.append("Trendline fan confirmation missing")

        direction = "buy" if structure_trend == "bullish" and pa_direction == "buy" else "sell" if structure_trend == "bearish" and pa_direction == "sell" else "none"
        confidence = min(100, score + (5 if pa_confidence >= 80 else 0))
        approved = direction != "none" and score >= self.config.minimum_trade_quality and confidence >= self.config.minimum_trade_confidence
        return self._result(approved, score, confidence, direction, reasons, warnings,
                            "Strategy conditions satisfied" if approved else "Strategy conditions failed")

    def _result(self, approved, score, confidence, direction, reasons, warnings, message):
        return StrategyResult(approved, min(max(score, 0), 100), min(max(confidence, 0), 100), direction, reasons, warnings, message)

    def no_trade(self, message):
        return self._result(False, 0, 0, "none", [], [message], message)

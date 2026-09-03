from dataclasses import dataclass

from modules.strategy_config import active_strategy


@dataclass
class StrategyResult:
    approved: bool
    score: int
    reasons: list
    warnings: list
    message: str


class StrategyEngine:
    def __init__(self):
        self.config = active_strategy

    def evaluate(self, structure, price_action, macd, market_context, timeframe=None):
        score = 0
        reasons = []
        warnings = []

        if structure is None:
            return self.no_trade("Structure unavailable")
        if price_action is None:
            return self.no_trade("Price action unavailable")
        if macd is None:
            return self.no_trade("MACD unavailable")
        if market_context is None:
            return self.no_trade("Market context unavailable")

        if timeframe is not None and timeframe not in self.config.allowed_timeframes:
            return self.no_trade("Timeframe not allowed")

        if self.config.require_structure:
            structure_quality = getattr(structure, "structure_quality", 0)
            if structure_quality >= self.config.minimum_structure_quality:
                score += 25
                reasons.append("Structure confirmed")
            else:
                warnings.append("Weak market structure")

        pattern_valid = getattr(price_action, "pattern_valid", False)
        pa_confidence = getattr(price_action, "confidence", 0)

        if self.config.require_pattern_confirmation:
            if pattern_valid and pa_confidence >= self.config.minimum_price_action_confidence:
                score += 30
                reasons.append("Price action confirmed")
            else:
                warnings.append("Price action not confirmed")

        if self.config.require_engulfing:
            engulfing = getattr(price_action, "engulfing", False)
            if not engulfing:
                warnings.append("Engulfing confirmation missing")
                return StrategyResult(
                    approved=False,
                    score=min(score, 100),
                    reasons=reasons,
                    warnings=warnings,
                    message="Required engulfing confirmation missing",
                )
            reasons.append("Engulfing confirmed")

        if self.config.use_macd_filter:
            macd_score = getattr(macd, "score", 0)
            macd_momentum = getattr(macd, "momentum_confirmation", False)

            if macd_score >= self.config.minimum_macd_score:
                score += 20
                reasons.append("MACD score accepted")
            else:
                warnings.append("MACD score weak")

            if self.config.require_macd_momentum:
                if macd_momentum:
                    score += 10
                    reasons.append("MACD momentum confirmed")
                else:
                    warnings.append("MACD momentum missing")

        context_confidence = getattr(market_context, "confidence", 0)
        if context_confidence >= 70:
            score += 15
            reasons.append("Market context strong")
        else:
            warnings.append("Market context weak")

        quality = min(score, 100)
        approved = quality >= self.config.minimum_trade_quality
        message = "Strategy conditions satisfied" if approved else "Strategy conditions failed"

        return StrategyResult(
            approved=approved,
            score=quality,
            reasons=reasons,
            warnings=warnings,
            message=message,
        )

    def no_trade(self, message):
        return StrategyResult(
            approved=False,
            score=0,
            reasons=[],
            warnings=[message],
            message=message,
        )

from dataclasses import dataclass, field


@dataclass
class DecisionResult:
    decision: str = "NO_TRADE"
    direction: str = "none"
    quality: int = 0
    confidence: int = 0
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    message: str = ""


class DecisionEngine:
    def __init__(self):
        self.minimum_quality = 60
        self.minimum_confidence = 60

    def analyze(self, structure, price_action, macd, market_context, news, risk=None):
        reasons = []
        warnings = []
        score = 0
        if structure is None:
            return self.no_trade("Structure unavailable")
        if price_action is None:
            return self.no_trade("Price action unavailable")
        if macd is None:
            return self.no_trade("MACD unavailable")
        if news is not None and getattr(news, "allow_trade", True) is False:
            return self.no_trade("Trading blocked by news filter")

        structure_quality = getattr(structure, "structure_quality", 0)
        structure_trend = getattr(structure, "trend", "unknown")
        if structure_trend in ("bullish", "bearish"):
            score += 25
            reasons.append(f"{structure_trend.title()} market structure")
        else:
            warnings.append("No directional structure")

        pa_direction = getattr(price_action, "direction", "none")
        pattern_valid = getattr(price_action, "pattern_valid", False)
        if pattern_valid:
            score += 25
            reasons.append("Valid price action setup")
        else:
            warnings.append("Price action pattern invalid")

        macd_trend = getattr(macd, "trend_confirmation", False)
        macd_momentum = getattr(macd, "momentum_confirmation", False)
        if macd_trend:
            score += 15
            reasons.append("MACD trend confirmation")
        else:
            warnings.append("MACD trend not confirmed")
        if macd_momentum:
            score += 10
            reasons.append("MACD momentum confirmed")
        if getattr(macd, "divergence", False):
            warnings.append("MACD divergence detected")

        context_confidence = getattr(market_context, "confidence", 0)
        context_trend = getattr(market_context, "trend", "unknown")
        if context_confidence >= 80:
            score += 15
            reasons.append("Strong market context")
        elif context_confidence >= 50:
            score += 5
        else:
            warnings.append("Weak market context")

        quality = min(max(score + min(structure_quality // 10, 10), 0), 100)
        confidence = self.calculate_confidence(quality, structure_trend, context_trend, pa_direction, macd_trend)

        if structure_trend == "bullish" and pa_direction == "buy":
            direction = "buy"
        elif structure_trend == "bearish" and pa_direction == "sell":
            direction = "sell"
        else:
            direction = "none"
            warnings.append("Structure and price action direction mismatch")

        if risk is not None and not getattr(risk, "allowed", False):
            return DecisionResult("NO_TRADE", direction, quality, confidence, reasons, warnings, "Trade rejected by risk manager")

        approved = direction != "none" and pattern_valid and quality >= self.minimum_quality and confidence >= self.minimum_confidence
        return DecisionResult(
            decision=("BUY" if direction == "buy" else "SELL") if approved else "NO_TRADE",
            direction=direction,
            quality=quality,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings,
            message="Trade setup approved" if approved else "Setup does not meet decision criteria",
        )

    def calculate_confidence(self, quality, structure_trend, context_trend, pa_direction, macd_trend):
        confidence = quality
        if structure_trend != "unknown" and structure_trend == context_trend:
            confidence += 5
        if (structure_trend == "bullish" and pa_direction == "buy") or (structure_trend == "bearish" and pa_direction == "sell"):
            confidence += 5
        if macd_trend:
            confidence += 5
        return min(max(confidence, 0), 100)

    def no_trade(self, message):
        return DecisionResult(warnings=[message], message=message)

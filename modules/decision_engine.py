from dataclasses import dataclass


@dataclass
class DecisionResult:

    decision: str

    direction: str

    quality: int

    confidence: int

    reasons: list

    warnings: list

    message: str


class DecisionEngine:

    def __init__(self):

        self.minimum_quality = 60

        self.minimum_confidence = 60

    def analyze(
        self,
        structure,
        price_action,
        macd,
        market_context,
        news,
        risk=None
    ):

        reasons = []
        warnings = []

        score = 0

        # ==========================================
        # BASIC VALIDATION
        # ==========================================

        if structure is None:

            return self.no_trade(
                "Structure unavailable"
            )

        if price_action is None:

            return self.no_trade(
                "Price action unavailable"
            )

        if macd is None:

            return self.no_trade(
                "MACD unavailable"
            )

        # ==========================================
        # NEWS FILTER
        # ==========================================

        if news is not None:

            if getattr(
                news,
                "allow_trade",
                True
            ) is False:

                return self.no_trade(
                    "Trading blocked by news filter"
                )

        # ==========================================
        # STRUCTURE
        # ==========================================

        structure_quality = getattr(
            structure,
            "structure_quality",
            0
        )

        structure_trend = getattr(
            structure,
            "trend",
            "unknown"
        )

        if structure_trend == "bullish":

            score += 25

            reasons.append(
                "Bullish market structure"
            )

        elif structure_trend == "bearish":

            score += 25

            reasons.append(
                "Bearish market structure"
            )

        else:

            warnings.append(
                "No directional structure"
            )

        # ==========================================
        # PRICE ACTION
        # ==========================================

        pa_direction = getattr(
            price_action,
            "direction",
            "none"
        )

        pa_confidence = getattr(
            price_action,
            "confidence",
            0
        )

        pattern_valid = getattr(
            price_action,
            "pattern_valid",
            False
        )

        if pattern_valid:

            score += 25

            reasons.append(
                "Valid price action setup"
            )

        else:

            warnings.append(
                "Price action pattern invalid"
            )

        # ==========================================
        # MACD
        # ==========================================

        macd_score = getattr(
            macd,
            "score",
            0
        )

        macd_trend = getattr(
            macd,
            "trend_confirmation",
            False
        )

        macd_momentum = getattr(
            macd,
            "momentum_confirmation",
            False
        )

        macd_divergence = getattr(
            macd,
            "divergence",
            False
        )

        if macd_trend:

            score += 15

            reasons.append(
                "MACD trend confirmation"
            )

        else:

            warnings.append(
                "MACD trend not confirmed"
            )

        if macd_momentum:

            score += 10

            reasons.append(
                "MACD momentum confirmed"
            )

        if macd_divergence:

            warnings.append(
                "MACD divergence detected"
            )

        # ==========================================
        # MARKET CONTEXT
        # ==========================================

        context_confidence = getattr(
            market_context,
            "confidence",
            0
        )

        context_trend = getattr(
            market_context,
            "trend",
            "unknown"
        )

        if context_confidence >= 80:

            score += 15

            reasons.append(
                "Strong market context"
            )

        elif context_confidence >= 50:

            score += 5

        else:

            warnings.append(
                "Weak market context"
            )

        # ==========================================
        # SCORE NORMALIZATION
        # ==========================================

        quality = min(
            max(score, 0),
            100
        )

        confidence = self.calculate_confidence(
            quality=quality,
            structure_trend=structure_trend,
            context_trend=context_trend,
            pa_direction=pa_direction,
            macd_trend=macd_trend
        )

        # ==========================================
        # DIRECTION VALIDATION
        # ==========================================

        direction = "none"

        if (
            structure_trend == "bullish"
            and
            pa_direction == "buy"
        ):

            direction = "buy"

        elif (
            structure_trend == "bearish"
            and
            pa_direction == "sell"
        ):

            direction = "sell"

        else:

            warnings.append(
                "Structure and price action direction mismatch"
            )

        # ==========================================
        # RISK VALIDATION
        # ==========================================

        if risk is not None:

            risk_allowed = getattr(
                risk,
                "allowed",
                False
            )

            if not risk_allowed:

                return DecisionResult(

                    decision="NO_TRADE",

                    direction=direction,

                    quality=quality,

                    confidence=confidence,

                    reasons=reasons,

                    warnings=warnings,

                    message=(
                        "Trade rejected by risk manager"
                    )
                )

        # ==========================================
        # FINAL DECISION
        # ==========================================

        if (
            direction != "none"
            and
            pattern_valid
            and
            quality >= self.minimum_quality
            and
            confidence >= self.minimum_confidence
        ):

            decision = (
                "BUY"
                if direction == "buy"
                else "SELL"
            )

            message = (
                "Trade setup approved"
            )

        else:

            decision = "NO_TRADE"

            message = (
                "Setup does not meet decision criteria"
            )

        return DecisionResult(

            decision=decision,

            direction=direction,

            quality=quality,

            confidence=confidence,

            reasons=reasons,

            warnings=warnings,

            message=message
        )

    # ==============================================
    # CONFIDENCE
    # ==============================================

    def calculate_confidence(
        self,
        quality,
        structure_trend,
        context_trend,
        pa_direction,
        macd_trend
    ):

        confidence = quality

        # Structure / context alignment

        if (
            structure_trend != "unknown"
            and
            structure_trend == context_trend
        ):

            confidence += 5

        # Price action alignment

        if (
            (
                structure_trend == "bullish"
                and
                pa_direction == "buy"
            )
            or
            (
                structure_trend == "bearish"
                and
                pa_direction == "sell"
            )
        ):

            confidence += 5

        # MACD confirmation

        if macd_trend:

            confidence += 5

        return min(
            confidence,
            100
        )

    # ==============================================
    # NO TRADE
    # ==============================================

    def no_trade(
        self,
        message
    ):

        return DecisionResult(

            decision="NO_TRADE",

            direction="none",

            quality=0,

            confidence=0,

            reasons=[],

            warnings=[message],

            message=message
        )

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



    def evaluate(
        self,
        structure,
        price_action,
        macd,
        market_context
    ):


        score = 0

        reasons = []

        warnings = []



        # =====================================
        # TIMEFRAME / STRUCTURE
        # =====================================

        if self.config.require_structure:


            structure_quality = getattr(
                structure,
                "structure_quality",
                0
            )


            if structure_quality >= self.config.minimum_structure_quality:

                score += 25

                reasons.append(
                    "Structure confirmed"
                )

            else:

                warnings.append(
                    "Weak market structure"
                )



        # =====================================
        # PRICE ACTION
        # =====================================

        pattern_valid = getattr(
            price_action,
            "pattern_valid",
            False
        )


        pa_confidence = getattr(
            price_action,
            "confidence",
            0
        )


        if self.config.require_pattern_confirmation:


            if (
                pattern_valid
                and
                pa_confidence >= self.config.minimum_price_action_confidence
            ):

                score += 30

                reasons.append(
                    "Price action confirmed"
                )

            else:

                warnings.append(
                    "Price action not confirmed"
                )



        # =====================================
        # MACD FILTER
        # =====================================

        if self.config.use_macd_filter:


            macd_score = getattr(
                macd,
                "score",
                0
            )


            macd_momentum = getattr(
                macd,
                "momentum_confirmation",
                False
            )


            if macd_score >= self.config.minimum_macd_score:

                score += 20

                reasons.append(
                    "MACD score accepted"
                )

            else:

                warnings.append(
                    "MACD score weak"
                )


            if self.config.require_macd_momentum:


                if macd_momentum:

                    score += 10

                    reasons.append(
                        "MACD momentum confirmed"
                    )

                else:

                    warnings.append(
                        "MACD momentum missing"
                    )



        # =====================================
        # MARKET CONTEXT
        # =====================================

        context_confidence = getattr(
            market_context,
            "confidence",
            0
        )


        if context_confidence >= 70:

            score += 15

            reasons.append(
                "Market context strong"
            )

        else:

            warnings.append(
                "Market context weak"
            )



        # =====================================
        # FINAL CHECK
        # =====================================

        approved = (

            score >= self.config.minimum_trade_quality

        )


        if approved:

            message = (
                "Strategy conditions satisfied"
            )

        else:

            message = (
                "Strategy conditions failed"
            )



        return StrategyResult(

            approved=approved,

            score=min(
                score,
                100
            ),

            reasons=reasons,

            warnings=warnings,

            message=message

        )

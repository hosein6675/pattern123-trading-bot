from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrendlineFanResult:
    direction: str = "none"
    aligned: bool = False
    score: int = 0
    support_slope: float = 0.0
    resistance_slope: float = 0.0
    support_price: float = 0.0
    resistance_price: float = 0.0
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class TrendlineFanAnalyzer:
    """Deterministic trendline-fan confirmation from confirmed swing points."""

    def analyze(self, structure, candles):
        if structure is None or not isinstance(candles, list) or len(candles) < 5:
            return TrendlineFanResult(warnings=["Trendline fan unavailable"])

        highs = getattr(structure, "swing_highs", [])
        lows = getattr(structure, "swing_lows", [])
        trend = getattr(structure, "trend", "unknown")
        if len(highs) < 2 or len(lows) < 2:
            return TrendlineFanResult(warnings=["Not enough swing points for trendline fan"])

        lh, rh = highs[-2], highs[-1]
        ll, rl = lows[-2], lows[-1]
        resistance_slope = self._slope(lh, rh)
        support_slope = self._slope(ll, rl)
        last_index = len(candles) - 1
        support_price = ll["price"] + support_slope * (last_index - ll["index"])
        resistance_price = lh["price"] + resistance_slope * (last_index - lh["index"])
        close = float(candles[-1]["close"])

        if trend == "bullish":
            aligned = support_slope > 0 and close >= support_price
            direction = "buy" if aligned else "none"
        elif trend == "bearish":
            aligned = resistance_slope < 0 and close <= resistance_price
            direction = "sell" if aligned else "none"
        else:
            aligned = False
            direction = "none"

        score = 20 if aligned else 0
        reasons = ["Trendline fan aligned with market structure"] if aligned else []
        warnings = [] if aligned else ["Trendline fan does not confirm current direction"]
        return TrendlineFanResult(direction, aligned, score, support_slope, resistance_slope,
                                  support_price, resistance_price, reasons, warnings)

    @staticmethod
    def _slope(first, second):
        dx = float(second["index"] - first["index"])
        if dx == 0:
            return 0.0
        return (float(second["price"]) - float(first["price"])) / dx

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StructureResult:
    trend: str = "unknown"
    swing_highs: List[Dict[str, Any]] = field(default_factory=list)
    swing_lows: List[Dict[str, Any]] = field(default_factory=list)
    bos: bool = False
    choch: bool = False
    last_bos_level: float = 0.0
    last_choch_level: float = 0.0
    impulse_leg: Dict[str, Any] = field(default_factory=dict)
    correction_leg: Dict[str, Any] = field(default_factory=dict)
    structure_quality: int = 0
    market_state: str = "no_data"
    description: str = ""


class StructureAnalyzer:
    """Deterministic swing/BOS/CHoCH structure analyzer."""

    def __init__(self, swing_window=2):
        self.swing_window = max(int(swing_window), 1)

    def analyze(self, candles):
        if not isinstance(candles, list) or len(candles) < self.swing_window * 2 + 5:
            return self.empty_result("Not enough candles")
        try:
            highs = [float(c["high"]) for c in candles]
            lows = [float(c["low"]) for c in candles]
        except (KeyError, TypeError, ValueError):
            return self.empty_result("Invalid candle data")

        highs_swings = []
        lows_swings = []
        w = self.swing_window
        for i in range(w, len(candles) - w):
            high = highs[i]
            low = lows[i]
            if high >= max(highs[i - w:i]) and high > max(highs[i + 1:i + w + 1]):
                highs_swings.append({"index": i, "price": high})
            if low <= min(lows[i - w:i]) and low < min(lows[i + 1:i + w + 1]):
                lows_swings.append({"index": i, "price": low})

        if len(highs_swings) < 2 or len(lows_swings) < 2:
            return StructureResult(
                swing_highs=highs_swings,
                swing_lows=lows_swings,
                market_state="insufficient_swings",
                description="Insufficient swing structure",
            )

        hh = highs_swings[-1]["price"] > highs_swings[-2]["price"]
        hl = lows_swings[-1]["price"] > lows_swings[-2]["price"]
        lh = highs_swings[-1]["price"] < highs_swings[-2]["price"]
        ll = lows_swings[-1]["price"] < lows_swings[-2]["price"]
        if hh and hl:
            trend = "bullish"
        elif lh and ll:
            trend = "bearish"
        else:
            trend = "range"

        last_close = float(candles[-1]["close"])
        prior_high = highs_swings[-1]["price"]
        prior_low = lows_swings[-1]["price"]
        bos = (trend == "bullish" and last_close > prior_high) or (trend == "bearish" and last_close < prior_low)
        choch = (trend == "bullish" and last_close < prior_low) or (trend == "bearish" and last_close > prior_high)

        if trend == "bullish":
            start, end = lows_swings[-2], highs_swings[-1]
            correction = {"start": highs_swings[-1]["price"], "end": lows_swings[-1]["price"]}
        elif trend == "bearish":
            start, end = highs_swings[-2], lows_swings[-1]
            correction = {"start": lows_swings[-1]["price"], "end": highs_swings[-1]["price"]}
        else:
            start, end, correction = highs_swings[-2], lows_swings[-1], {}

        quality = 40 + (25 if trend in ("bullish", "bearish") else 0)
        quality += 20 if bos else 0
        quality += 15 if len(highs_swings) >= 3 and len(lows_swings) >= 3 else 0

        return StructureResult(
            trend=trend,
            swing_highs=highs_swings,
            swing_lows=lows_swings,
            bos=bos,
            choch=choch,
            last_bos_level=prior_high if trend == "bullish" else prior_low,
            last_choch_level=prior_low if trend == "bullish" else prior_high,
            impulse_leg={"start": start["price"], "end": end["price"], "start_index": start["index"], "end_index": end["index"]},
            correction_leg=correction,
            structure_quality=min(quality, 100),
            market_state="trend" if trend in ("bullish", "bearish") else "range",
            description="Swing structure with BOS/CHoCH detection",
        )

    def empty_result(self, reason):
        return StructureResult(market_state="no_data", description=reason)

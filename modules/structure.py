from dataclasses import dataclass

@dataclass
class StructureResult:


trend: str
swing_highs: list
swing_lows: list
bos: bool
choch: bool
last_bos_level: float
last_choch_level: float
impulse_leg: dict
correction_leg: dict
structure_quality: int
market_state: str
description: str


class StructureAnalyzer:


def analyze(self, candles):

    if not candles or len(candles) < 30:
        return self.empty_result(
            "Not enough candles"
        )

    swing_highs = []
    swing_lows = []

    for i in range(2, len(candles) - 2):

        try:
            high = float(candles[i]["high"])
            low = float(candles[i]["low"])

            high_1 = float(candles[i - 1]["high"])
            high_2 = float(candles[i - 2]["high"])
            high_plus_1 = float(candles[i + 1]["high"])
            high_plus_2 = float(candles[i + 2]["high"])

            low_1 = float(candles[i - 1]["low"])
            low_2 = float(candles[i - 2]["low"])
            low_plus_1 = float(candles[i + 1]["low"])
            low_plus_2 = float(candles[i + 2]["low"])

        except (
            KeyError,
            TypeError,
            ValueError
        ):
            continue

        if (
            high > high_1
            and high > high_plus_1
            and high > high_2
            and high > high_plus_2
        ):
            swing_highs.append({
                "index": i,
                "price": high
            })

        if (
            low < low_1
            and low < low_plus_1
            and low < low_2
            and low < low_plus_2
        ):
            swing_lows.append({
                "index": i,
                "price": low
            })

    trend = "range"
    bos = False
    choch = False

    last_bos = 0.0
    last_choch = 0.0

    quality = 0

    if (
        len(swing_highs) >= 2
        and len(swing_lows) >= 2
    ):

        last_high = swing_highs[-1]["price"]
        prev_high = swing_highs[-2]["price"]

        last_low = swing_lows[-1]["price"]
        prev_low = swing_lows[-2]["price"]

        if (
            last_high > prev_high
            and last_low > prev_low
        ):
            trend = "bullish"
            quality += 30

        elif (
            last_high < prev_high
            and last_low < prev_low
        ):
            trend = "bearish"
            quality += 30

    if trend == "bullish" and swing_highs:

        current_high = max(
            float(candles[-1]["high"]),
            float(candles[-1]["close"])
        )

        if current_high > swing_highs[-1]["price"]:

            bos = True

            last_bos = (
                swing_highs[-1]["price"]
            )

    elif trend == "bearish" and swing_lows:

        current_low = min(
            float(candles[-1]["low"]),
            float(candles[-1]["close"])
        )

        if current_low < swing_lows[-1]["price"]:

            bos = True

            last_bos = (
                swing_lows[-1]["price"]
            )

    if (
        trend == "bullish"
        and len(swing_lows) >= 2
    ):

        if (
            swing_lows[-1]["price"]
            <
            swing_lows[-2]["price"]
        ):

            choch = True

            last_choch = (
                swing_lows[-1]["price"]
            )

    elif (
        trend == "bearish"
        and len(swing_highs) >= 2
    ):

        if (
            swing_highs[-1]["price"]
            >
            swing_highs[-2]["price"]
        ):

            choch = True

            last_choch = (
                swing_highs[-1]["price"]
            )

    if bos:
        quality += 25

    if len(swing_highs) >= 3:
        quality += 20

    if len(swing_lows) >= 3:
        quality += 20

    if choch:
        quality -= 15

    quality = max(
        0,
        min(
            quality,
            100
        )
    )

    if trend == "bullish":

        if choch:
            market_state = "bullish_warning"
        else:
            market_state = "bullish"

    elif trend == "bearish":

        if choch:
            market_state = "bearish_warning"
        else:
            market_state = "bearish"

    else:

        market_state = "range"

    impulse = self.get_impulse_leg(
        candles,
        trend
    )

    correction = self.get_correction_leg(
        candles,
        trend
    )

    return StructureResult(

        trend=trend,

        swing_highs=swing_highs,

        swing_lows=swing_lows,

        bos=bos,

        choch=choch,

        last_bos_level=last_bos,

        last_choch_level=last_choch,

        impulse_leg=impulse,

        correction_leg=correction,

        structure_quality=quality,

        market_state=market_state,

        description=(
            "Validated market structure analysis"
        )

    )

def get_impulse_leg(
    self,
    candles,
    trend
):

    if not candles or len(candles) < 20:
        return {}

    try:

        if trend == "bullish":

            start = float(
                candles[-20]["low"]
            )

            end = float(
                candles[-5]["high"]
            )

        elif trend == "bearish":

            start = float(
                candles[-20]["high"]
            )

            end = float(
                candles[-5]["low"]
            )

        else:

            start = float(
                candles[-20]["close"]
            )

            end = float(
                candles[-5]["close"]
            )

        return {

            "start": start,

            "end": end,

            "direction": trend

        }

    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError
    ):

        return {}

def get_correction_leg(
    self,
    candles,
    trend
):

    if not candles or len(candles) < 5:
        return {}

    try:

        start = float(
            candles[-5]["close"]
        )

        end = float(
            candles[-1]["close"]
        )

        return {

            "start": start,

            "end": end,

            "direction": (
                "correction"
                if trend in (
                    "bullish",
                    "bearish"
                )
                else "unknown"
            )

        }

    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError
    ):

        return {}

def empty_result(
    self,
    reason
):

    return StructureResult(

        trend="unknown",

        swing_highs=[],

        swing_lows=[],

        bos=False,

        choch=False,

        last_bos_level=0.0,

        last_choch_level=0.0,

        impulse_leg={},

        correction_leg={},

        structure_quality=0,

        market_state="no_data",

        description=reason

    )

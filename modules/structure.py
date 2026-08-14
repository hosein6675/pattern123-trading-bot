from dataclasses import dataclass


@dataclass
class StructureResult:

    trend: str

    highs: list

    lows: list

    bos: bool

    choch: bool

    structure_state: str

    description: str



class StructureAnalyzer:


    def analyze(self, candles):


        if isinstance(candles, dict):

            # اولویت ساختار با M15
            candles = candles.get(
                "M15",
                []
            )


        if len(candles) < 20:

            return StructureResult(

                trend="unknown",

                highs=[],

                lows=[],

                bos=False,

                choch=False,

                structure_state="no_data",

                description="Not enough candles"

            )



        highs = []

        lows = []



        for i in range(2, len(candles)-2):


            current_high = candles[i]["high"]

            current_low = candles[i]["low"]


            if (
                current_high > candles[i-1]["high"]
                and current_high > candles[i+1]["high"]
            ):

                highs.append(current_high)



            if (
                current_low < candles[i-1]["low"]
                and current_low < candles[i+1]["low"]
            ):

                lows.append(current_low)



        trend = "range"

        bos = False

        choch = False

        state = "range"



        if len(highs) >= 2 and len(lows) >= 2:


            # ساختار صعودی

            if (
                highs[-1] > highs[-2]
                and lows[-1] > lows[-2]
            ):

                trend = "bullish"

                state = "bullish_continuation"

                bos = True



            # ساختار نزولی

            elif (
                highs[-1] < highs[-2]
                and lows[-1] < lows[-2]
            ):

                trend = "bearish"

                state = "bearish_continuation"

                bos = True



        # تشخیص تغییر رفتار ساده

        if len(highs) >= 2 and len(lows) >= 2:


            if (
                trend == "bullish"
                and lows[-1] < lows[-2]
            ):

                choch = True

                state = "possible_bearish_reversal"



            elif (
                trend == "bearish"
                and highs[-1] > highs[-2]
            ):

                choch = True

                state = "possible_bullish_reversal"



        return StructureResult(

            trend=trend,

            highs=highs,

            lows=lows,

            bos=bos,

            choch=choch,

            structure_state=state,

            description="Structure analyzed with BOS and CHoCH"

        )

from dataclasses import dataclass


@dataclass
class StructureResult:

    trend: str

    highs: list

    lows: list

    bos: bool

    reversal: bool

    description: str



class StructureAnalyzer:


    def analyze(self, candles):


        if isinstance(candles, dict):

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

                reversal=False,

                description="Not enough candles"

            )



        highs = []

        lows = []



        for i in range(2, len(candles)-2):


            high = candles[i]["high"]

            low = candles[i]["low"]



            if (
                high > candles[i-1]["high"]
                and high > candles[i+1]["high"]
            ):

                highs.append(high)



            if (
                low < candles[i-1]["low"]
                and low < candles[i+1]["low"]
            ):

                lows.append(low)



        trend = "range"

        if len(highs) >= 2 and len(lows) >= 2:


            if highs[-1] > highs[-2] and lows[-1] > lows[-2]:

                trend = "bullish"



            elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:

                trend = "bearish"



        bos = False

        reversal = False



        if trend == "bullish":

            bos = True


        elif trend == "bearish":

            bos = True



        return StructureResult(

            trend=trend,

            highs=highs,

            lows=lows,

            bos=bos,

            reversal=reversal,

            description="Structure analyzed"

        )

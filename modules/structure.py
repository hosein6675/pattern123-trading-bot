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

            return StructureResult(

                trend="unknown",

                swing_highs=[],

                swing_lows=[],

                bos=False,

                choch=False,

                last_bos_level=0,

                last_choch_level=0,

                impulse_leg={},

                correction_leg={},

                structure_quality=0,

                market_state="no_data",

                description="Not enough candles"

            )


        swing_highs = []

        swing_lows = []


        # پیدا کردن Swing های معتبر

        for i in range(2, len(candles)-2):


            high = candles[i]["high"]

            low = candles[i]["low"]


            if (

                high > candles[i-1]["high"]

                and high > candles[i+1]["high"]

                and high > candles[i-2]["high"]

                and high > candles[i+2]["high"]

            ):

                swing_highs.append(

                    {

                        "index": i,

                        "price": high

                    }

                )



            if (

                low < candles[i-1]["low"]

                and low < candles[i+1]["low"]

                and low < candles[i-2]["low"]

                and low < candles[i+2]["low"]

            ):

                swing_lows.append(

                    {

                        "index": i,

                        "price": low

                    }

                )



        trend = "range"

        bos = False

        choch = False

        last_bos = 0

        last_choch = 0



        quality = 0



        # تشخیص روند

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:


            last_high = swing_highs[-1]["price"]

            prev_high = swing_highs[-2]["price"]


            last_low = swing_lows[-1]["price"]

            prev_low = swing_lows[-2]["price"]



            # روند صعودی

            if (

                last_high > prev_high

                and last_low > prev_low

            ):

                trend = "bullish"

                quality += 30



                # BOS صعودی

                bos = True

                last_bos = last_high



            # روند نزولی

            elif (

                last_high < prev_high

                and last_low < prev_low

            ):

                trend = "bearish"

                quality += 30



                # BOS نزولی

                bos = True

                last_bos = last_low



        # تشخیص CHoCH

        if trend == "bullish" and len(swing_lows) >= 2:


            if swing_lows[-1]["price"] < swing_lows[-2]["price"]:

                choch = True

                last_choch = swing_lows[-1]["price"]



        elif trend == "bearish" and len(swing_highs) >= 2:


            if swing_highs[-1]["price"] > swing_highs[-2]["price"]:

                choch = True

                last_choch = swing_highs[-1]["price"]



        # قدرت ساختار

        if bos:

            quality += 25


        if len(swing_highs) >= 3:

            quality += 20


        if len(swing_lows) >= 3:

            quality += 20



        if quality > 100:

            quality = 100



        impulse = self.get_impulse_leg(

            candles

        )


        correction = self.get_correction_leg(

            candles

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

            market_state=trend,

            description="Advanced structure analysis"

        )



    def get_impulse_leg(self, candles):


        return {

            "start": candles[-20]["close"],

            "end": candles[-5]["close"]

        }



    def get_correction_leg(self, candles):


        return {

            "start": candles[-5]["close"],

            "end": candles[-1]["close"]

        }

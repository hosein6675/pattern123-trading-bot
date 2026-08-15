from dataclasses import dataclass



@dataclass
class EntrySignal:

    direction: str

    entry: float

    stop_loss: float

    tp1: float

    tp2: float

    tp3: float

    confidence: int

    point3_zone: float

    engulfing: bool

    pattern_valid: bool

    description: str





class PriceActionEngine:


    def analyze(self, structure, candles):


        if not candles or len(candles) < 20:

            return self.empty_signal(
                "Not enough candles"
            )



        point3 = self.find_point3(

            structure,

            candles

        )


        if point3 is None:

            return self.empty_signal(

                "Point 3 not found"

            )



        zone = self.calculate_50_zone(

            structure,

            point3

        )


        candle = candles[-1]


        engulfing = self.check_engulfing(

            candles

        )



        direction = "none"

        confidence = 0



        entry = 0

        stop = 0

        tp1 = 0

        tp2 = 0

        tp3 = 0



        # سناریوی خرید

        if (

            structure.trend == "bullish"

            and engulfing

        ):

            direction = "buy"

            confidence += 40



            entry = candle["close"]


            stop = point3


            risk = entry - stop


            if risk > 0:


                tp1 = entry + risk

                tp2 = entry + (risk * 2)

                tp3 = entry + (risk * 3)



        # سناریوی فروش

        elif (

            structure.trend == "bearish"

            and engulfing

        ):

            direction = "sell"

            confidence += 40



            entry = candle["close"]


            stop = point3


            risk = stop - entry



            if risk > 0:


                tp1 = entry - risk

                tp2 = entry - (risk * 2)

                tp3 = entry - (risk * 3)



        if engulfing:

            confidence += 20



        if zone:

            confidence += 20



        if structure.bos:

            confidence += 20



        if confidence > 100:

            confidence = 100



        return EntrySignal(

            direction=direction,

            entry=entry,

            stop_loss=stop,

            tp1=tp1,

            tp2=tp2,

            tp3=tp3,

            confidence=confidence,

            point3_zone=zone,

            engulfing=engulfing,

            pattern_valid=direction != "none",

            description="123 Pattern + Point3 + 50% Zone analysis"

        )





    def find_point3(self, structure, candles):


        if structure.swing_lows and structure.trend == "bullish":


            return structure.swing_lows[-1]["price"]



        if structure.swing_highs and structure.trend == "bearish":


            return structure.swing_highs[-1]["price"]



        return None





    def calculate_50_zone(self, structure, point3):


        try:


            if structure.impulse_leg:


                start = structure.impulse_leg["start"]

                end = structure.impulse_leg["end"]


                zone = (

                    start + end

                ) / 2



                return zone



        except:

            pass



        return 0





    def check_engulfing(self, candles):


        if len(candles) < 2:

            return False



        previous = candles[-2]

        current = candles[-1]



        bullish = (

            current["close"] > current["open"]

            and

            previous["close"] < previous["open"]

            and

            current["close"] > previous["open"]

            and

            current["open"] < previous["close"]

        )



        bearish = (

            current["close"] < current["open"]

            and

            previous["close"] > previous["open"]

            and

            current["open"] > previous["close"]

            and

            current["close"] < previous["open"]

        )



        return bullish or bearish





    def empty_signal(self, reason):


        return EntrySignal(

            direction="none",

            entry=0,

            stop_loss=0,

            tp1=0,

            tp2=0,

            tp3=0,

            confidence=0,

            point3_zone=0,

            engulfing=False,

            pattern_valid=False,

            description=reason

        )

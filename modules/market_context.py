from dataclasses import dataclass



@dataclass
class MarketContext:

    symbol: str

    trend: str

    structure: str

    last_leg: str

    correction: str

    fib_zone: str

    phase: str

    market_condition: str

    support_resistance: str

    liquidity: str

    session: str

    confidence: int



class MarketContextAnalyzer:


    def analyze(self, candles, symbol):


        # دریافت دیتا از چند تایم فریم

        if isinstance(candles, dict):

            daily = candles.get(
                "D1",
                []
            )

            h4 = candles.get(
                "H4",
                []
            )

        else:

            daily = candles

            h4 = candles



        if len(daily) < 20 or len(h4) < 20:

            return MarketContext(

                symbol=symbol,

                trend="unknown",

                structure="not_enough_data",

                last_leg="unknown",

                correction="unknown",

                fib_zone="unknown",

                phase="waiting",

                market_condition="unknown",

                support_resistance="unknown",

                liquidity="unknown",

                session="unknown",

                confidence=0

            )



        d1_trend = self.detect_trend(
            daily
        )


        h4_trend = self.detect_trend(
            h4
        )



        trend = d1_trend


        phase = "continuation"



        if d1_trend == h4_trend:

            trend = d1_trend

            phase = "trend_continuation"



        elif d1_trend != h4_trend:

            trend = d1_trend

            phase = "correction"



        confidence = 50


        if d1_trend == h4_trend:

            confidence = 80



        return MarketContext(

            symbol=symbol,

            trend=trend,

            structure=h4_trend,

            last_leg=h4_trend,

            correction="yes" if phase == "correction" else "no",

            fib_zone="pending",

            phase=phase,

            market_condition="normal",

            support_resistance="pending",

            liquidity="pending",

            session="unknown",

            confidence=confidence

        )



    def detect_trend(self, candles):


        highs = []

        lows = []


        for candle in candles:


            highs.append(
                candle["high"]
            )


            lows.append(
                candle["low"]
            )



        if len(highs) < 5:

            return "unknown"



        if highs[-1] > highs[-5] and lows[-1] > lows[-5]:

            return "bullish"



        if highs[-1] < highs[-5] and lows[-1] < lows[-5]:

            return "bearish"



        return "range"

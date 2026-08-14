from dataclasses import dataclass



@dataclass
class MACDResult:

    trend_confirmation: bool

    divergence: bool

    hidden_divergence: bool

    momentum_confirmation: bool

    score: int

    description: str





class MACDEngine:


    def analyze(self, candles):


        if len(candles) < 35:

            return MACDResult(

                trend_confirmation=False,

                divergence=False,

                hidden_divergence=False,

                momentum_confirmation=False,

                score=0,

                description="Not enough candles"

            )



        closes = [

            candle["close"]

            for candle in candles

        ]



        ema12 = self.calculate_ema(

            closes,

            12

        )


        ema26 = self.calculate_ema(

            closes,

            26

        )



        macd_line = ema12 - ema26



        signal = self.calculate_signal(

            closes

        )



        score = 0



        trend_confirmation = False

        momentum_confirmation = False



        if macd_line > signal:

            trend_confirmation = True

            score += 40



        else:

            score -= 20



        if abs(macd_line) > abs(signal):

            momentum_confirmation = True

            score += 30



        divergence = self.detect_divergence(

            candles

        )



        if divergence:

            score += 15



        if score < 0:

            score = 0



        return MACDResult(

            trend_confirmation=trend_confirmation,

            divergence=divergence,

            hidden_divergence=False,

            momentum_confirmation=momentum_confirmation,

            score=min(score,100),

            description="MACD analyzed"

        )



    def calculate_ema(
        self,
        prices,
        period
    ):


        if len(prices) < period:

            return 0



        multiplier = 2 / (period + 1)


        ema = sum(

            prices[:period]

        ) / period



        for price in prices[period:]:

            ema = (

                (price - ema)

                *

                multiplier

            ) + ema



        return ema



    def calculate_signal(
        self,
        prices
    ):


        ema12 = self.calculate_ema(

            prices,

            12

        )


        ema26 = self.calculate_ema(

            prices,

            26

        )


        return ema12 - ema26



    def detect_divergence(
        self,
        candles
    ):


        if len(candles) < 10:

            return False



        recent = candles[-5:]

        old = candles[-10:-5]



        recent_high = max(

            c["high"]

            for c in recent

        )


        old_high = max(

            c["high"]

            for c in old

        )


        recent_close = recent[-1]["close"]

        old_close = old[-1]["close"]



        if (

            recent_high > old_high

            and

            recent_close < old_close

        ):

            return True



        return False

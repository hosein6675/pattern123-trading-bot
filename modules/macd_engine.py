from dataclasses import dataclass


@dataclass
class MACDResult:

    trend_confirmation: bool

    divergence: bool

    hidden_divergence: bool

    momentum_confirmation: bool

    score: int

    macd_line: float

    signal_line: float

    histogram: float

    description: str


class MACDEngine:

    def __init__(self):

        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9

    def analyze(self, candles):

        if not candles or len(candles) < 40:

            return self.empty_result(
                "Not enough candles"
            )

        closes = [
            float(candle["close"])
            for candle in candles
        ]

        macd_values = self.calculate_macd_series(
            closes
        )

        if len(macd_values) < self.signal_period:

            return self.empty_result(
                "Not enough MACD data"
            )

        macd_line = macd_values[-1]

        signal_line = self.calculate_ema(
            macd_values,
            self.signal_period
        )

        histogram = (
            macd_line - signal_line
        )

        trend_confirmation = (
            macd_line > signal_line
        )

        momentum_confirmation = (
            histogram > 0
        )

        score = 0

        # ==========================================
        # TREND
        # ==========================================

        if trend_confirmation:

            score += 40

        else:

            score -= 20

        # ==========================================
        # MOMENTUM
        # ==========================================

        if momentum_confirmation:

            score += 30

        # ==========================================
        # DIVERGENCE
        # ==========================================

        divergence = self.detect_divergence(
            candles,
            macd_values
        )

        if divergence:

            score += 15

        # ==========================================
        # HISTOGRAM STRENGTH
        # ==========================================

        if len(macd_values) >= 2:

            previous_macd = macd_values[-2]

            previous_signal = self.calculate_ema(
                macd_values[:-1],
                self.signal_period
            )

            previous_histogram = (
                previous_macd - previous_signal
            )

            if abs(histogram) > abs(
                previous_histogram
            ):

                score += 15

        score = max(
            0,
            min(score, 100)
        )

        return MACDResult(

            trend_confirmation=(
                trend_confirmation
            ),

            divergence=divergence,

            hidden_divergence=False,

            momentum_confirmation=(
                momentum_confirmation
            ),

            score=score,

            macd_line=round(
                macd_line,
                8
            ),

            signal_line=round(
                signal_line,
                8
            ),

            histogram=round(
                histogram,
                8
            ),

            description="MACD 12/26/9 analysis"
        )

    # ==============================================
    # MACD SERIES
    # ==============================================

    def calculate_macd_series(
        self,
        prices
    ):

        if len(prices) < self.slow_period:

            return []

        ema_fast = self.calculate_ema_series(
            prices,
            self.fast_period
        )

        ema_slow = self.calculate_ema_series(
            prices,
            self.slow_period
        )

        offset = (
            self.slow_period
            - self.fast_period
        )

        fast_aligned = ema_fast[
            offset:
        ]

        macd_values = []

        for fast, slow in zip(
            fast_aligned,
            ema_slow
        ):

            macd_values.append(
                fast - slow
            )

        return macd_values

    # ==============================================
    # EMA SERIES
    # ==============================================

    def calculate_ema_series(
        self,
        prices,
        period
    ):

        if len(prices) < period:

            return []

        multiplier = (
            2 / (period + 1)
        )

        ema = sum(
            prices[:period]
        ) / period

        result = [ema]

        for price in prices[period:]:

            ema = (
                (price - ema)
                * multiplier
            ) + ema

            result.append(ema)

        return result

    # ==============================================
    # SINGLE EMA
    # ==============================================

    def calculate_ema(
        self,
        prices,
        period
    ):

        if len(prices) < period:

            return 0.0

        multiplier = (
            2 / (period + 1)
        )

        ema = sum(
            prices[:period]
        ) / period

        for price in prices[period:]:

            ema = (
                (price - ema)
                * multiplier
            ) + ema

        return ema

    # ==============================================
    # DIVERGENCE
    # ==============================================

    def detect_divergence(
        self,
        candles,
        macd_values
    ):

        if (
            len(candles) < 20
            or
            len(macd_values) < 10
        ):

            return False

        recent = candles[-5:]
        previous = candles[-10:-5]

        recent_high = max(
            candle["high"]
            for candle in recent
        )

        previous_high = max(
            candle["high"]
            for candle in previous
        )

        recent_low = min(
            candle["low"]
            for candle in recent
        )

        previous_low = min(
            candle["low"]
            for candle in previous
        )

        macd_recent = macd_values[-1]

        macd_previous = macd_values[-6]

        # Bearish divergence
        bearish_divergence = (
            recent_high > previous_high
            and
            macd_recent < macd_previous
        )

        # Bullish divergence
        bullish_divergence = (
            recent_low < previous_low
            and
            macd_recent > macd_previous
        )

        return (
            bullish_divergence
            or
            bearish_divergence
        )

    # ==============================================
    # EMPTY RESULT
    # ==============================================

    def empty_result(
        self,
        reason
    ):

        return MACDResult(

            trend_confirmation=False,

            divergence=False,

            hidden_divergence=False,

            momentum_confirmation=False,

            score=0,

            macd_line=0.0,

            signal_line=0.0,

            histogram=0.0,

            description=reason
        )

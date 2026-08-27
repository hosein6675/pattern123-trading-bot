from dataclasses import dataclass


@dataclass
class MACDResult:
    trend_confirmation: bool = False
    divergence: bool = False
    hidden_divergence: bool = False
    momentum_confirmation: bool = False
    score: int = 0
    macd_line: float = 0.0
    signal_line: float = 0.0
    histogram: float = 0.0
    description: str = ""


class MACDEngine:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = int(fast_period)
        self.slow_period = int(slow_period)
        self.signal_period = int(signal_period)

    def analyze(self, candles):
        if not isinstance(candles, list) or len(candles) < 40:
            return self.empty_result("Not enough candles")
        try:
            closes = [float(candle["close"]) for candle in candles]
        except (KeyError, TypeError, ValueError):
            return self.empty_result("Invalid candle data")
        macd_values = self.calculate_macd_series(closes)
        if len(macd_values) < self.signal_period:
            return self.empty_result("Not enough MACD data")
        macd_line = macd_values[-1]
        signal_line = self.calculate_ema(macd_values, self.signal_period)
        histogram = macd_line - signal_line
        trend_confirmation = macd_line > signal_line
        momentum_confirmation = histogram > 0
        divergence = self.detect_divergence(candles, macd_values)
        score = 0
        if trend_confirmation:
            score += 40
        if momentum_confirmation:
            score += 30
        if divergence:
            score += 15
        if len(macd_values) >= 2:
            previous_signal = self.calculate_ema(macd_values[:-1], self.signal_period)
            previous_histogram = macd_values[-2] - previous_signal
            if abs(histogram) > abs(previous_histogram):
                score += 15
        return MACDResult(
            trend_confirmation=trend_confirmation,
            divergence=divergence,
            hidden_divergence=False,
            momentum_confirmation=momentum_confirmation,
            score=min(max(score, 0), 100),
            macd_line=round(macd_line, 8),
            signal_line=round(signal_line, 8),
            histogram=round(histogram, 8),
            description="MACD 12/26/9 analysis",
        )

    def calculate_macd_series(self, prices):
        if len(prices) < self.slow_period:
            return []
        ema_fast = self.calculate_ema_series(prices, self.fast_period)
        ema_slow = self.calculate_ema_series(prices, self.slow_period)
        offset = self.slow_period - self.fast_period
        return [fast - slow for fast, slow in zip(ema_fast[offset:], ema_slow)]

    def calculate_ema_series(self, prices, period):
        if len(prices) < period:
            return []
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        result = [ema]
        for price in prices[period:]:
            ema = ((price - ema) * multiplier) + ema
            result.append(ema)
        return result

    def calculate_ema(self, prices, period):
        if len(prices) < period:
            return 0.0
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = ((price - ema) * multiplier) + ema
        return ema

    def detect_divergence(self, candles, macd_values):
        if len(candles) < 20 or len(macd_values) < 10:
            return False
        try:
            recent = candles[-5:]
            previous = candles[-10:-5]
            recent_high = max(float(c["high"]) for c in recent)
            previous_high = max(float(c["high"]) for c in previous)
            recent_low = min(float(c["low"]) for c in recent)
            previous_low = min(float(c["low"]) for c in previous)
        except (KeyError, TypeError, ValueError):
            return False
        macd_recent = macd_values[-1]
        macd_previous = macd_values[-6]
        return (
            (recent_high > previous_high and macd_recent < macd_previous)
            or (recent_low < previous_low and macd_recent > macd_previous)
        )

    def empty_result(self, reason):
        return MACDResult(description=reason)

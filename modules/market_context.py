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


class MarketContextAnalyzer:

    def analyze(self, candles, symbol):

        if len(candles) < 50:
            return MarketContext(
                symbol=symbol,
                trend="unknown",
                structure="not_enough_data",
                last_leg="unknown",
                correction="unknown",
                fib_zone="unknown",
                phase="waiting"
            )

        return MarketContext(
            symbol=symbol,
            trend="analysis_pending",
            structure="analysis_pending",
            last_leg="analysis_pending",
            correction="analysis_pending",
            fib_zone="analysis_pending",
            phase="ready_for_strategy"
        )

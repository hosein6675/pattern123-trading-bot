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


        if len(candles) < 50:

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



        return MarketContext(

            symbol=symbol,

            trend="analysis_pending",

            structure="analysis_pending",

            last_leg="analysis_pending",

            correction="analysis_pending",

            fib_zone="analysis_pending",

            phase="ready_for_strategy",

            market_condition="pending",

            support_resistance="pending",

            liquidity="pending",

            session="pending",

            confidence=0

        )

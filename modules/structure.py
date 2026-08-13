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

        if len(candles) < 20:
            return StructureResult(
                trend="unknown",
                highs=[],
                lows=[],
                bos=False,
                reversal=False,
                description="Not enough candles"
            )

        return StructureResult(
            trend="pending",
            highs=[],
            lows=[],
            bos=False,
            reversal=False,
            description="Structure engine ready"
        )

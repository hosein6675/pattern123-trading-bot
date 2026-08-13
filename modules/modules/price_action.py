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


class PriceActionEngine:

    def analyze(self, context, candles):

        return EntrySignal(
            direction="none",
            entry=0,
            stop_loss=0,
            tp1=0,
            tp2=0,
            tp3=0,
            confidence=0
        )

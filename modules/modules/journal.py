from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradeRecord:
    symbol: str
    timeframe: str
    direction: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    result: str
    profit_loss: float
    reason: str
    analysis_note: str
    created_at: str


class JournalEngine:

    def create_record(
        self,
        symbol,
        timeframe,
        direction,
        entry,
        stop_loss,
        tp1,
        tp2,
        tp3
    ):

        return TradeRecord(
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            result="pending",
            profit_loss=0,
            reason="",
            analysis_note="",
            created_at=str(datetime.utcnow())
        )

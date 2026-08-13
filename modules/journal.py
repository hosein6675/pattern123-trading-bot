from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradeRecord:

    symbol: str
    timeframe: str
    direction: str

    entry_price: float
    exit_price: float

    stop_loss: float
    take_profit: float

    entry_time: str
    exit_time: str

    result: str
    profit_loss: float

    reason: str
    analysis: str



class JournalEngine:


    def __init__(self):

        self.trades = []



    def add_trade(self, trade):

        self.trades.append(trade)



    def create_trade(

        self,
        symbol,
        timeframe,
        direction,
        entry_price,
        exit_price,
        stop_loss,
        take_profit,
        result,
        profit_loss,
        reason,
        analysis

    ):


        now = datetime.now()


        trade = TradeRecord(

            symbol=symbol,

            timeframe=timeframe,

            direction=direction,

            entry_price=entry_price,

            exit_price=exit_price,

            stop_loss=stop_loss,

            take_profit=take_profit,

            entry_time=str(now),

            exit_time=str(now),

            result=result,

            profit_loss=profit_loss,

            reason=reason,

            analysis=analysis

        )


        self.add_trade(trade)


        return trade



    def get_history(self):

        return self.trades

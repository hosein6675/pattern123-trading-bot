from dataclasses import dataclass
from datetime import datetime



@dataclass
class AccountState:

    balance: float

    equity: float

    peak_balance: float

    daily_start_balance: float

    daily_profit_loss: float

    drawdown_percent: float

    updated_at: str



class AccountManager:


    def __init__(self):

        self.balance = 1000.0

        self.equity = 1000.0

        self.peak_balance = 1000.0

        self.daily_start_balance = 1000.0



    def get_account(self):


        drawdown = 0


        if self.peak_balance > 0:

            drawdown = (
                (
                    self.peak_balance - self.equity
                )
                /
                self.peak_balance
            ) * 100



        return AccountState(

            balance=self.balance,

            equity=self.equity,

            peak_balance=self.peak_balance,

            daily_start_balance=self.daily_start_balance,

            daily_profit_loss=(
                self.equity -
                self.daily_start_balance
            ),

            drawdown_percent=round(
                drawdown,
                2
            ),

            updated_at=str(
                datetime.utcnow()
            )

        )



    def update_balance(self, new_balance):


        self.balance = new_balance

        self.equity = new_balance



        if new_balance > self.peak_balance:

            self.peak_balance = new_balance



    def new_trading_day(self):


        self.daily_start_balance = self.equity



    def update_equity(self, equity):


        self.equity = equity



        if equity > self.peak_balance:

            self.peak_balance = equity

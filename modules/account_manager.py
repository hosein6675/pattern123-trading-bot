from dataclasses import dataclass


@dataclass
class AccountInfo:

    balance: float
    equity: float
    mode: str



class AccountManager:


    def __init__(self):

        # حساب دمو اولیه
        self.balance = 1000.0
        self.equity = 1000.0
        self.mode = "demo"



    def get_account(self):

        return AccountInfo(

            balance=self.balance,

            equity=self.equity,

            mode=self.mode

        )



    def update_balance(self, new_balance):

        self.balance = new_balance


        self.equity = new_balance

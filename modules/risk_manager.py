from dataclasses import dataclass
from datetime import datetime



@dataclass
class RiskResult:

    allowed: bool

    risk_percent: float

    risk_amount: float

    lot_size: float

    daily_drawdown: float

    quality_adjustment: str

    message: str





class RiskManager:


    def __init__(self):

        self.base_risk_percent = 1.0

        self.max_daily_drawdown_percent = 3.0

        self.start_day_balance = None

        self.current_daily_loss = 0

        self.day = datetime.now().date()

        self.max_open_positions = 3





    def update_day(self, balance):

        today = datetime.now().date()


        if today != self.day:

            self.day = today

            self.start_day_balance = balance

            self.current_daily_loss = 0



        if self.start_day_balance is None:

            self.start_day_balance = balance





    def calculate_risk_percent(self, quality):


        if quality >= 90:

            return 1.0, "High quality setup"


        elif quality >= 75:

            return 0.75, "Medium quality setup"


        elif quality >= 60:

            return 0.5, "Low risk setup"


        else:

            return 0, "Setup quality too low"





    def calculate_lot_size(

        self,

        balance,

        entry,

        stop_loss,

        risk_amount

    ):


        distance = abs(entry - stop_loss)


        if distance == 0:

            return 0



        lot = risk_amount / distance


        return round(lot, 2)





    def check(

        self,

        balance,

        entry=0,

        stop_loss=0,

        quality=0,

        loss_amount=0,

        open_positions=0

    ):


        self.update_day(balance)



        self.current_daily_loss += loss_amount



        daily_drawdown = (

            self.current_daily_loss /

            self.start_day_balance

        ) * 100



        if daily_drawdown >= self.max_daily_drawdown_percent:


            return RiskResult(

                allowed=False,

                risk_percent=0,

                risk_amount=0,

                lot_size=0,

                daily_drawdown=daily_drawdown,

                quality_adjustment="",

                message="Daily drawdown limit reached"

            )



        if open_positions >= self.max_open_positions:


            return RiskResult(

                allowed=False,

                risk_percent=0,

                risk_amount=0,

                lot_size=0,

                daily_drawdown=daily_drawdown,

                quality_adjustment="",

                message="Maximum open positions reached"

            )



        risk_percent, quality_msg = self.calculate_risk_percent(

            quality

        )



        if risk_percent == 0:


            return RiskResult(

                allowed=False,

                risk_percent=0,

                risk_amount=0,

                lot_size=0,

                daily_drawdown=daily_drawdown,

                quality_adjustment=quality_msg,

                message="Trade rejected by quality filter"

            )



        risk_amount = (

            balance *

            risk_percent /

            100

        )



        lot_size = self.calculate_lot_size(

            balance,

            entry,

            stop_loss,

            risk_amount

        )



        return RiskResult(

            allowed=True,

            risk_percent=risk_percent,

            risk_amount=risk_amount,

            lot_size=lot_size,

            daily_drawdown=daily_drawdown,

            quality_adjustment=quality_msg,

            message="Risk approved"

        )

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskResult:

    allowed: bool
    risk_amount: float
    daily_drawdown: float
    message: str



class RiskManager:


    def __init__(self):

        # درصد ریسک هر معامله
        self.trade_risk_percent = 1.0

        # حداکثر دراداون روزانه
        self.max_daily_drawdown_percent = 3.0

        # موجودی ابتدای روز
        self.start_day_balance = None

        # ضرر ثبت شده امروز
        self.current_daily_loss = 0

        # تاریخ روز کاری
        self.day = datetime.now().date()



    def update_day(self, balance):

        today = datetime.now().date()

        # شروع روز جدید
        if today != self.day:

            self.day = today
            self.start_day_balance = balance
            self.current_daily_loss = 0


        # اولین اجرا
        if self.start_day_balance is None:

            self.start_day_balance = balance



    def calculate_risk(self, balance):

        self.update_day(balance)

        risk_amount = (
            self.start_day_balance *
            self.trade_risk_percent /
            100
        )

        return risk_amount



    def check(self, balance, loss_amount=0, position_size=0):

        self.update_day(balance)


        # اضافه کردن ضرر معامله
        self.current_daily_loss += loss_amount



        # محاسبه درصد دراداون روزانه
        daily_drawdown = (

            self.current_daily_loss /
            self.start_day_balance

        ) * 100



        # مقدار ریسک مجاز معامله
        risk_amount = self.calculate_risk(balance)



        # بررسی محدودیت ضرر روزانه
        if daily_drawdown >= self.max_daily_drawdown_percent:

            return RiskResult(

                allowed=False,

                risk_amount=risk_amount,

                daily_drawdown=daily_drawdown,

                message="Daily drawdown limit reached"

            )



        return RiskResult(

            allowed=True,

            risk_amount=risk_amount,

            daily_drawdown=daily_drawdown,

            message="Risk approved"

        )

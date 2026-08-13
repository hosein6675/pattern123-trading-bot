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

        # درصد ریسک هر معامله نسبت به موجودی ابتدای روز
        self.trade_risk_percent = 1.0

        # حداکثر دراودان روزانه نسبت به موجودی ابتدای روز
        self.daily_drawdown_percent = 3.0

        self.day_start_balance = None
        self.current_day = None


    def update_day(self, balance):

        today = datetime.now().date()

        # شروع روز کاری جدید
        if self.current_day != today:

            self.current_day = today
            self.day_start_balance = balance



    def check(self, balance, current_equity):

        # بررسی شروع روز
        self.update_day(balance)


        # مقدار ضرر امروز
        daily_loss = (
            self.day_start_balance - current_equity
        )


        # درصد دراودان امروز
        daily_drawdown = (
            daily_loss / self.day_start_balance
        ) * 100



        # حد مجاز ضرر روزانه
        max_loss = (
            self.day_start_balance *
            self.daily_drawdown_percent / 100
        )



        # اگر حد ضرر روزانه پر شده باشد
        if daily_loss >= max_loss:

            return RiskResult(
                allowed=False,
                risk_amount=0,
                daily_drawdown=daily_drawdown,
                message="Daily drawdown limit reached"
            )



        # مقدار ریسک معامله بر اساس سرمایه ابتدای روز
        risk_amount = (
            self.day_start_balance *
            self.trade_risk_percent / 100
        )



        return RiskResult(
            allowed=True,
            risk_amount=risk_amount,
            daily_drawdown=daily_drawdown,
            message="Risk approved"
        )

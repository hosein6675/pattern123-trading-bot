from dataclasses import dataclass


@dataclass
class RiskStatus:
    allowed: bool
    reason: str
    daily_drawdown: float
    weekly_drawdown: float
    monthly_drawdown: float


class RiskManager:

    def __init__(
        self,
        daily_limit=5,
        weekly_limit=12,
        monthly_limit=15
    ):
        self.daily_limit = daily_limit
        self.weekly_limit = weekly_limit
        self.monthly_limit = monthly_limit


    def check(
        self,
        daily_drawdown,
        weekly_drawdown,
        monthly_drawdown
    ):

        if daily_drawdown >= self.daily_limit:
            return RiskStatus(
                False,
                "Daily drawdown limit reached",
                daily_drawdown,
                weekly_drawdown,
                monthly_drawdown
            )

        if weekly_drawdown >= self.weekly_limit:
            return RiskStatus(
                False,
                "Weekly drawdown limit reached",
                daily_drawdown,
                weekly_drawdown,
                monthly_drawdown
            )

        if monthly_drawdown >= self.monthly_limit:
            return RiskStatus(
                False,
                "Monthly drawdown limit reached",
                daily_drawdown,
                weekly_drawdown,
                monthly_drawdown
            )


        return RiskStatus(
            True,
            "Risk check passed",
            daily_drawdown,
            weekly_drawdown,
            monthly_drawdown
        )

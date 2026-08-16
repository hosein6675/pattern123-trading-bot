from dataclasses import dataclass
from datetime import datetime

from modules.config import active_config


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

        self.max_daily_drawdown_percent = (
            active_config.daily_drawdown_limit
        )

        self.start_day_balance = None
        self.current_daily_loss = 0.0
        self.day = datetime.now().date()

        self.max_open_positions = (
            active_config.max_open_positions
        )

    def update_day(self, balance):
        today = datetime.now().date()

        if today != self.day:
            self.day = today
            self.start_day_balance = balance
            self.current_daily_loss = 0.0

        if self.start_day_balance is None:
            self.start_day_balance = balance

    def register_loss(self, loss_amount):
        if loss_amount is None:
            return

        try:
            loss_amount = float(loss_amount)
        except (TypeError, ValueError):
            return

        if loss_amount <= 0:
            return

        self.current_daily_loss += loss_amount

    def calculate_daily_drawdown(self, balance):
        if (
            self.start_day_balance is None
            or self.start_day_balance <= 0
        ):
            return 0.0

        drawdown = (
            self.current_daily_loss
            / self.start_day_balance
        ) * 100

        return round(
            max(drawdown, 0.0),
            2
        )

    def calculate_risk_percent(self, quality):
        try:
            quality = float(quality)
        except (TypeError, ValueError):
            return 0.0, "Invalid setup quality"

        if quality >= 90:
            return 1.0, "High quality setup"

        if quality >= 75:
            return 0.75, "Medium quality setup"

        if quality >= 60:
            return 0.5, "Low risk setup"

        return 0.0, "Setup quality too low"

    def calculate_lot_size(
        self,
        balance,
        entry,
        stop_loss,
        risk_amount
    ):
        try:
            balance = float(balance)
            entry = float(entry)
            stop_loss = float(stop_loss)
            risk_amount = float(risk_amount)
        except (TypeError, ValueError):
            return 0.0

        if balance <= 0:
            return 0.0

        if risk_amount <= 0:
            return 0.0

        if entry <= 0 or stop_loss <= 0:
            return 0.0

        distance = abs(entry - stop_loss)

        if distance <= 0:
            return 0.0

        lot = risk_amount / distance

        return round(
            max(lot, 0.0),
            2
        )

    def check(
        self,
        balance,
        entry=0,
        stop_loss=0,
        quality=0,
        loss_amount=0,
        open_positions=0
    ):
        try:
            balance = float(balance)
        except (TypeError, ValueError):
            return RiskResult(
                allowed=False,
                risk_percent=0.0,
                risk_amount=0.0,
                lot_size=0.0,
                daily_drawdown=0.0,
                quality_adjustment="",
                message="Invalid account balance"
            )

        if balance <= 0:
            return RiskResult(
                allowed=False,
                risk_percent=0.0,
                risk_amount=0.0,
                lot_size=0.0,
                daily_drawdown=0.0,
                quality_adjustment="",
                message="Account balance must be greater than zero"
            )

        try:
            open_positions = int(open_positions)
        except (TypeError, ValueError):
            open_positions = 0

        if open_positions < 0:
            open_positions = 0

        self.update_day(balance)

        daily_drawdown = self.calculate_daily_drawdown(
            balance
        )

        if (
            daily_drawdown
            >= self.max_daily_drawdown_percent
        ):
            return RiskResult(
                allowed=False,
                risk_percent=0.0,
                risk_amount=0.0,
                lot_size=0.0,
                daily_drawdown=daily_drawdown,
                quality_adjustment="",
                message="Daily drawdown limit reached"
            )

        if (
            open_positions
            >= self.max_open_positions
        ):
            return RiskResult(
                allowed=False,
                risk_percent=0.0,
                risk_amount=0.0,
                lot_size=0.0,
                daily_drawdown=daily_drawdown,
                quality_adjustment="",
                message="Maximum open positions reached"
            )

        risk_percent, quality_message = (
            self.calculate_risk_percent(quality)
        )

        if risk_percent <= 0:
            return RiskResult(
                allowed=False,
                risk_percent=0.0,
                risk_amount=0.0,
                lot_size=0.0,
                daily_drawdown=daily_drawdown,
                quality_adjustment=quality_message,
                message="Trade rejected by quality filter"
            )

        risk_amount = (
            balance
            * risk_percent
            / 100.0
        )

        lot_size = self.calculate_lot_size(
            balance=balance,
            entry=entry,
            stop_loss=stop_loss,
            risk_amount=risk_amount
        )

        if lot_size <= 0:
            return RiskResult(
                allowed=False,
                risk_percent=risk_percent,
                risk_amount=risk_amount,
                lot_size=0.0,
                daily_drawdown=daily_drawdown,
                quality_adjustment=quality_message,
                message="Invalid entry or stop loss"
            )

        return RiskResult(
            allowed=True,
            risk_percent=risk_percent,
            risk_amount=round(
                risk_amount,
                2
            ),
            lot_size=lot_size,
            daily_drawdown=daily_drawdown,
            quality_adjustment=quality_message,
            message="Risk approved"
        )

from dataclasses import dataclass
from datetime import datetime
import math

from modules.config import active_config


@dataclass(frozen=True)
class RiskResult:
    allowed: bool
    risk_percent: float
    risk_amount: float
    lot_size: float
    daily_drawdown: float
    account_drawdown: float
    total_risk_percent: float
    consecutive_losses: int
    quality_adjustment: str
    message: str


class RiskManager:
    """Deterministic money-management guardrail for demo and live execution."""

    def __init__(self):
        self.base_risk_percent = active_config.risk_per_trade_percent
        self.max_daily_drawdown_percent = active_config.daily_drawdown_limit
        self.max_account_drawdown_percent = active_config.max_account_drawdown
        self.max_total_risk_percent = active_config.max_total_risk_percent
        self.max_open_positions = active_config.max_open_positions
        self.max_consecutive_losses = active_config.max_consecutive_losses
        self.start_day_balance = None
        self.current_daily_loss = 0.0
        self.consecutive_losses = 0
        self.day = datetime.now().date()
        self.peak_equity = None

    def update_day(self, balance):
        today = datetime.now().date()
        if today != self.day:
            self.day = today
            self.start_day_balance = float(balance)
            self.current_daily_loss = 0.0
            self.consecutive_losses = 0
        if self.start_day_balance is None:
            self.start_day_balance = float(balance)

    def register_loss(self, loss_amount):
        try:
            loss_amount = float(loss_amount)
        except (TypeError, ValueError):
            return
        if loss_amount > 0:
            self.current_daily_loss += loss_amount
            self.consecutive_losses += 1

    def register_trade_result(self, pnl):
        """Record a closed trade result; reset the loss streak after a profit."""
        try:
            pnl = float(pnl)
        except (TypeError, ValueError):
            return
        if pnl < 0:
            self.register_loss(abs(pnl))
        elif pnl > 0:
            self.consecutive_losses = 0

    def calculate_daily_drawdown(self, balance=0, equity=None):
        if not self.start_day_balance or self.start_day_balance <= 0:
            return 0.0
        realized = max(self.current_daily_loss / self.start_day_balance * 100, 0.0)
        floating = 0.0
        if equity is not None:
            try:
                floating = max((self.start_day_balance - float(equity)) / self.start_day_balance * 100, 0.0)
            except (TypeError, ValueError):
                floating = 0.0
        return round(max(realized, floating), 2)

    def calculate_account_drawdown(self, balance, equity=None):
        if equity is None:
            return 0.0
        try:
            balance = float(balance)
            equity = float(equity)
        except (TypeError, ValueError):
            return 0.0
        if balance <= 0:
            return 0.0
        if self.peak_equity is None:
            self.peak_equity = max(balance, equity)
        else:
            self.peak_equity = max(self.peak_equity, balance, equity)
        return round(max((self.peak_equity - equity) / self.peak_equity * 100, 0.0), 2)

    def calculate_risk_percent(self, quality):
        try:
            quality = float(quality)
        except (TypeError, ValueError):
            return 0.0, "Invalid setup quality"
        if quality >= 90:
            return min(self.base_risk_percent, 1.0), "High quality setup"
        if quality >= 75:
            return min(self.base_risk_percent, 0.75), "Medium quality setup"
        if quality >= 60:
            return min(self.base_risk_percent, 0.5), "Low risk setup"
        return 0.0, "Setup quality too low"

    @staticmethod
    def _normalize_lot(lot, minimum, maximum, step):
        if lot <= 0 or minimum <= 0 or maximum <= 0 or step <= 0:
            return 0.0
        lot = min(lot, maximum)
        if lot < minimum:
            return 0.0
        steps = math.floor((lot + 1e-12) / step)
        normalized = steps * step
        if normalized < minimum:
            return 0.0
        return round(min(normalized, maximum), 8)

    def calculate_lot_size(
        self,
        balance,
        entry,
        stop_loss,
        risk_amount,
        risk_per_lot=None,
        min_lot=None,
        max_lot=None,
        lot_step=None,
    ):
        try:
            balance = float(balance)
            entry = float(entry)
            stop_loss = float(stop_loss)
            risk_amount = float(risk_amount)
        except (TypeError, ValueError):
            return 0.0
        if balance <= 0 or risk_amount <= 0 or entry <= 0 or stop_loss <= 0:
            return 0.0

        if risk_per_lot is None or float(risk_per_lot) <= 0:
            distance = abs(entry - stop_loss)
            risk_per_lot = distance
        try:
            risk_per_lot = float(risk_per_lot)
        except (TypeError, ValueError):
            return 0.0
        if risk_per_lot <= 0:
            return 0.0

        minimum = float(min_lot if min_lot is not None else active_config.min_lot)
        maximum = float(max_lot if max_lot is not None else active_config.max_lot)
        step = float(lot_step if lot_step is not None else active_config.lot_step)
        raw_lot = risk_amount / risk_per_lot
        return self._normalize_lot(raw_lot, minimum, maximum, step)

    def check(
        self,
        balance,
        entry=0,
        stop_loss=0,
        quality=0,
        loss_amount=0,
        open_positions=0,
        equity=None,
        risk_per_lot=None,
        total_risk_percent=0.0,
        min_lot=None,
        max_lot=None,
        lot_step=None,
    ):
        try:
            balance = float(balance)
        except (TypeError, ValueError):
            return self._reject("Invalid account balance")
        if balance <= 0:
            return self._reject("Account balance must be greater than zero")

        if loss_amount:
            self.register_loss(loss_amount)
        self.update_day(balance)
        daily_drawdown = self.calculate_daily_drawdown(balance, equity)
        account_drawdown = self.calculate_account_drawdown(balance, equity)

        if daily_drawdown >= self.max_daily_drawdown_percent:
            return self._reject("Daily drawdown limit reached", daily_drawdown, account_drawdown, total_risk_percent)
        if account_drawdown >= self.max_account_drawdown_percent:
            return self._reject("Maximum account drawdown reached", daily_drawdown, account_drawdown, total_risk_percent)
        if self.consecutive_losses >= self.max_consecutive_losses:
            return self._reject("Maximum consecutive losses reached", daily_drawdown, account_drawdown, total_risk_percent)

        try:
            open_positions = max(int(open_positions), 0)
            total_risk_percent = max(float(total_risk_percent), 0.0)
        except (TypeError, ValueError):
            open_positions = 0
            total_risk_percent = 0.0

        if open_positions >= self.max_open_positions:
            return self._reject("Maximum open positions reached", daily_drawdown, account_drawdown, total_risk_percent)

        risk_percent, quality_message = self.calculate_risk_percent(quality)
        if risk_percent <= 0:
            return RiskResult(False, 0.0, 0.0, 0.0, daily_drawdown, account_drawdown, total_risk_percent, self.consecutive_losses, quality_message, "Trade rejected by quality filter")

        if total_risk_percent + risk_percent > self.max_total_risk_percent + 1e-12:
            return self._reject("Maximum total portfolio risk reached", daily_drawdown, account_drawdown, total_risk_percent)

        risk_amount = balance * risk_percent / 100.0
        lot_size = self.calculate_lot_size(
            balance, entry, stop_loss, risk_amount, risk_per_lot,
            min_lot, max_lot, lot_step
        )
        if lot_size <= 0:
            return RiskResult(False, risk_percent, round(risk_amount, 2), 0.0, daily_drawdown, account_drawdown, total_risk_percent, self.consecutive_losses, quality_message, "Position size is below broker constraints")

        return RiskResult(
            True,
            risk_percent,
            round(risk_amount, 2),
            lot_size,
            daily_drawdown,
            account_drawdown,
            round(total_risk_percent + risk_percent, 2),
            self.consecutive_losses,
            quality_message,
            "Risk approved",
        )

    def _reject(self, message, daily_drawdown=0.0, account_drawdown=0.0, total_risk_percent=0.0):
        return RiskResult(False, 0.0, 0.0, 0.0, daily_drawdown, account_drawdown, total_risk_percent, self.consecutive_losses, "", message)

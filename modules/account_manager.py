from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
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
        drawdown = 0.0
        if self.peak_balance > 0:
            drawdown = max((self.peak_balance - self.equity) / self.peak_balance * 100, 0.0)
        return AccountState(
            balance=self.balance,
            equity=self.equity,
            peak_balance=self.peak_balance,
            daily_start_balance=self.daily_start_balance,
            daily_profit_loss=self.equity - self.daily_start_balance,
            drawdown_percent=round(drawdown, 2),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def sync_from_broker(self, snapshot):
        """Apply a broker account snapshot without silently fabricating values."""
        if not snapshot or snapshot.get("status") not in ("ready", "connected"):
            return False
        try:
            balance = float(snapshot.get("balance", self.balance))
            equity = float(snapshot.get("equity", self.equity))
        except (TypeError, ValueError):
            return False
        if balance < 0 or equity < 0:
            return False
        self.balance = balance
        self.equity = equity
        self.peak_balance = max(self.peak_balance, balance, equity)
        return True

    def update_balance(self, new_balance):
        new_balance = float(new_balance)
        if new_balance < 0:
            raise ValueError("balance must be non-negative")
        self.balance = new_balance
        self.equity = new_balance
        self.peak_balance = max(self.peak_balance, new_balance)

    def new_trading_day(self):
        self.daily_start_balance = self.equity

    def update_equity(self, equity):
        equity = float(equity)
        if equity < 0:
            raise ValueError("equity must be non-negative")
        self.equity = equity
        self.peak_balance = max(self.peak_balance, equity)

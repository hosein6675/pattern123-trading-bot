from dataclasses import dataclass


@dataclass
class BotConfig:

    mode: str = "demo"

    market: str = "forex"

    symbol: str = "XAUUSD"

    timeframe: str = "H1"

    trade_news: bool = False

    initial_balance: float = 1000

    daily_drawdown_limit: float = 5

    weekly_drawdown_limit: float = 12

    monthly_drawdown_limit: float = 15


active_config = BotConfig()

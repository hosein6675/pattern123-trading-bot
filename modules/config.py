from dataclasses import dataclass



@dataclass
class BotConfig:


    # وضعیت حساب

    mode: str = "demo"



    # بازار فعال

    market: str = "forex"



    # نماد اصلی فعال

    symbol: str = "XAUUSD"



    # نمادهای مجاز

    allowed_symbols: list = None



    # تایم فریم

    timeframe: str = "H1"



    # معامله با اخبار

    trade_news: bool = False



    # سرمایه شروع دمو

    initial_balance: float = 1000.0



    # محدودیت های ضرر

    daily_drawdown_limit: float = 5.0

    weekly_drawdown_limit: float = 12.0

    monthly_drawdown_limit: float = 15.0



    # کنترل معاملات

    auto_trading: bool = False

    max_open_positions: int = 1



    # حالت تست

    backtest_mode: bool = True



    # اتصال آینده

    broker_connection: str = "none"

    # none / mt5 / api



    # ماژول هوش مصنوعی جدا

    ai_trading_mode: bool = False



    def __post_init__(self):

        if self.allowed_symbols is None:

            self.allowed_symbols = [

                self.symbol

            ]



    def is_symbol_allowed(self, symbol):

        return symbol in self.allowed_symbols





active_config = BotConfig()

from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.journal import JournalEngine
from modules.account_manager import AccountManager
from modules.market_context import MarketContextAnalyzer
from modules.news_filter import NewsFilter
from modules.order_manager import OrderManager
from modules.market_data import MarketDataEngine
from modules.config import active_config


class TradingEngine:


    def __init__(self):

        self.context = MarketContextAnalyzer()

        self.structure = StructureAnalyzer()

        self.price_action = PriceActionEngine()

        self.macd = MACDEngine()

        self.risk = RiskManager()

        self.journal = JournalEngine()

        self.account = AccountManager()

        self.news = NewsFilter()

        self.orders = OrderManager()

        self.market_data = MarketDataEngine()



    def analyze_market(self, symbol):


        account = self.account.get_account()



        if not active_config.is_symbol_allowed(symbol):

            return {

                "symbol": symbol,

                "status": "symbol_not_allowed"

            }



        news_status = self.news.check_news(symbol)



        if (
            news_status.has_news
            and news_status.impact == "high"
            and active_config.trade_news is False
        ):

            return {

                "symbol": symbol,

                "news": news_status,

                "status": "trade_blocked_news"

            }



        # دریافت دیتای چند تایم فریم از MT5

        market_data = self.market_data.get_multi_timeframe(
            symbol
        )


        trend_data = {

            "D1": market_data["trend_daily"],

            "H4": market_data["trend_h4"]

        }


        structure_data = {

            "H4": market_data["trend_h4"],

            "H1": market_data["structure_h1"],

            "M15": market_data["structure_m15"]

        }


        entry_data = {

            "M15": market_data["structure_m15"],

            "M5": market_data["entry_m5"],

            "M1": market_data["entry_m1"]

        }



        # فعلاً ارسال به موتورهای موجود

        market_context = self.context.analyze(

            trend_data,

            symbol

        )


        structure_result = self.structure.analyze(

            structure_data

        )


        pa_result = self.price_action.analyze(

            structure_result,

            entry_data

        )


        macd_result = self.macd.analyze(

            entry_data["M15"]

        )



        risk_result = self.risk.check(

            balance=account.balance,

            loss_amount=0,

            position_size=0

        )



        return {


            "symbol": symbol,

            "account": account,

            "news": news_status,

            "market_context": market_context,

            "structure": structure_result,

            "price_action": pa_result,

            "macd": macd_result,

            "risk": risk_result

        }



    def execute_order(

        self,

        symbol,

        direction,

        volume,

        stop_loss,

        take_profit

    ):


        return self.orders.execute_trade(

            symbol,

            direction,

            volume,

            stop_loss,

            take_profit

        )

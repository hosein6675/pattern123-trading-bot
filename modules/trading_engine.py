from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.journal import JournalEngine
from modules.account_manager import AccountManager
from modules.market_context import MarketContextAnalyzer
from modules.news_filter import NewsFilter
from modules.order_manager import OrderManager
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



    def analyze_market(self, symbol, timeframe, candles):


        account = self.account.get_account()



        # بررسی قفل نماد

        if not active_config.is_symbol_allowed(symbol):

            return {

                "symbol": symbol,

                "timeframe": timeframe,

                "account": account,

                "status": "symbol_not_allowed"

            }



        # بررسی خبر

        news_status = self.news.check_news(symbol)



        if (
            news_status.has_news
            and news_status.impact == "high"
            and active_config.trade_news is False
        ):

            return {

                "symbol": symbol,

                "timeframe": timeframe,

                "account": account,

                "news": news_status,

                "status": "trade_blocked_news"

            }



        market_context = self.context.analyze(

            candles,

            symbol

        )



        structure_result = self.structure.analyze(

            candles

        )



        pa_result = self.price_action.analyze(

            structure_result,

            candles

        )



        macd_result = self.macd.analyze(

            candles

        )



        risk_result = self.risk.check(

            balance=account.balance,

            loss_amount=0,

            position_size=0

        )



        return {


            "symbol": symbol,

            "timeframe": timeframe,

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

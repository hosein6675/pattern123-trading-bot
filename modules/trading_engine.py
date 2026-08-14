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



    def analyze_market(
        self,
        symbol,
        timeframe=None,
        candles=None
    ):


        account = self.account.get_account()



        if not active_config.is_symbol_allowed(symbol):

            return {

                "symbol": symbol,

                "status": "symbol_not_allowed"

            }



        # اگر کندل ارسال نشده بود، از MT5 بگیر

        if not candles:

            candles_result = self.market_data.get_candles(

                symbol,

                timeframe or active_config.timeframe,

                days=200

            )


            candles = candles_result["candles"]



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

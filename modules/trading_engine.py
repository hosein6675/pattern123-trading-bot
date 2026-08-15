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
from modules.decision_engine import DecisionEngine
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

        self.decision = DecisionEngine()



    def analyze_market(
        self,
        symbol,
        timeframe=None,
        candles=None
    ):

        timeframe = (
            timeframe
            or active_config.timeframe
        )


        account = self.account.get_account()



        if not active_config.is_symbol_allowed(symbol):

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Symbol not allowed"
            )



        if candles is None:

            market = self.market_data.get_candles(
                symbol,
                timeframe,
                days=200
            )


            if market.get("status") != "ready":

                return self.no_trade(
                    symbol,
                    timeframe,
                    account,
                    "Market data unavailable"
                )


            candles = market.get(
                "candles",
                []
            )



        if len(candles) < 50:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Not enough candles"
            )



        news = self.news.check_news(
            symbol
        )


        if not news.allow_trade:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "News blocked trade"
            )



        context = self.context.analyze(
            candles,
            symbol
        )


        structure = self.structure.analyze(
            candles
        )


        price_action = self.price_action.analyze(
            structure,
            candles
        )


        macd = self.macd.analyze(
            candles
        )



        decision = self.decision.analyze(

            structure=structure,

            price_action=price_action,

            macd=macd,

            market_context=context,

            news=news

        )



        positions = self.orders.get_open_positions()


        if positions is None:

            positions = []



        risk = self.risk.check(

            balance=account.balance,

            entry=price_action.entry,

            stop_loss=price_action.stop_loss,

            quality=decision.quality,

            loss_amount=0,

            open_positions=len(
                positions
            )

        )



        final_decision = self.decision.analyze(

            structure=structure,

            price_action=price_action,

            macd=macd,

            market_context=context,

            news=news,

            risk=risk

        )



        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "status": "analysis_complete",

            "account": account,

            "market_context": context,

            "structure": structure,

            "price_action": price_action,

            "macd": macd,

            "news": news,

            "risk": risk,

            "decision": final_decision,

            "open_positions": len(
                positions
            )

        }




    def execute_order(
        self,
        symbol,
        direction,
        volume,
        stop_loss,
        take_profit
    ):


        if direction not in (
            "buy",
            "sell"
        ):

            return {

                "success": False,

                "message":
                "Invalid direction"

            }



        return self.orders.execute_trade(

            symbol=symbol,

            direction=direction,

            volume=volume,

            stop_loss=stop_loss,

            take_profit=take_profit

        )




    def close_order(
        self,
        order_id
    ):

        return self.orders.close_trade(
            order_id
        )




    def get_open_positions(self):

        return self.orders.get_open_positions()




    def no_trade(
        self,
        symbol,
        timeframe,
        account,
        reason
    ):

        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "status": reason,

            "account": account,

            "decision": "NO_TRADE"

        }

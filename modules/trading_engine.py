
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
from modules.strategy_engine import StrategyEngine


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

        self.strategy = StrategyEngine()


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


        # ==========================================
        # 1. SYMBOL VALIDATION
        # ==========================================

        if not active_config.is_symbol_allowed(symbol):

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Symbol not allowed"
            )


        # ==========================================
        # 2. TIMEFRAME VALIDATION
        # ==========================================

        if timeframe not in (
            "M1",
            "M5",
            "M15",
            "H1",
            "H4",
            "D1"
        ):

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Unsupported timeframe"
            )


        # ==========================================
        # 3. MARKET DATA
        # ==========================================

        if candles is None:

            market = self.market_data.get_candles(
                symbol,
                timeframe,
                days=200
            )

            if not market:

                return self.no_trade(
                    symbol,
                    timeframe,
                    account,
                    "Market data unavailable"
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


        if not candles:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "No candles available"
            )


        if len(candles) < 50:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Not enough candles"
            )


        # ==========================================
        # 4. NEWS FILTER
        # ==========================================

        news = self.news.check_news(
            symbol
        )


        if news is not None:

            if not getattr(
                news,
                "allow_trade",
                True
            ):

                return self.no_trade(
                    symbol,
                    timeframe,
                    account,
                    "News blocked trade"
                )


        # ==========================================
        # 5. MARKET CONTEXT
        # ==========================================

        context = self.context.analyze(
            candles,
            symbol
        )


        if context is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Market context unavailable"
            )


        # ==========================================
        # 6. MARKET STRUCTURE
        # ==========================================

        structure = self.structure.analyze(
            candles
        )


        if structure is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Market structure unavailable"
            )


        # ==========================================
        # 7. PRICE ACTION
        # ==========================================

        price_action = self.price_action.analyze(
            structure,
            candles
        )


        if price_action is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Price action unavailable"
            )


        # ==========================================
        # 8. MACD
        # ==========================================

        macd = self.macd.analyze(
            candles
        )


        if macd is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "MACD unavailable"
            )


        # ==========================================
        # 9. STRATEGY ENGINE
        # ==========================================

        strategy_result = self.strategy.evaluate(

            structure=structure,

            price_action=price_action,

            macd=macd,

            market_context=context

        )


        if strategy_result is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Strategy evaluation failed"
            )


        if not getattr(
            strategy_result,
            "approved",
            False
        ):

            return {

                "symbol": symbol,

                "timeframe": timeframe,

                "status": "strategy_rejected",

                "account": account,

                "market_context": context,

                "structure": structure,

                "price_action": price_action,

                "macd": macd,

                "strategy": strategy_result,

                "news": news,

                "decision": "NO_TRADE",

                "open_positions": 0

            }


        # ==========================================
        # 10. INITIAL DECISION
        # ==========================================

        decision = self.decision.analyze(

            structure=structure,

            price_action=price_action,

            macd=macd,

            market_context=context,

            news=news

        )


        if decision is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Decision engine failed"
            )


        # ==========================================
        # 11. OPEN POSITIONS
        # ==========================================

        positions = self.orders.get_open_positions()


        if positions is None:

            positions = []


        # ==========================================
        # 12. ENTRY / STOP LOSS
        # ==========================================

        entry = getattr(
            price_action,
            "entry",
            0
        )

        stop_loss = getattr(
            price_action,
            "stop_loss",
            0
        )


        # ==========================================
        # 13. RISK CHECK
        # ==========================================

        risk = self.risk.check(

            balance=getattr(
                account,
                "balance",
                0
            ),

            entry=entry,

            stop_loss=stop_loss,

            quality=getattr(
                decision,
                "quality",
                0
            ),

            loss_amount=0,

            open_positions=len(
                positions
            )

        )


        if risk is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Risk manager failed"
            )


        # ==========================================
        # 14. FINAL DECISION
        # ==========================================

        final_decision = self.decision.analyze(

            structure=structure,

            price_action=price_action,

            macd=macd,

            market_context=context,

            news=news,

            risk=risk

        )


        if final_decision is None:

            return self.no_trade(
                symbol,
                timeframe,
                account,
                "Final decision failed"
            )


        # ==========================================
        # 15. FINAL RESULT
        # ==========================================

        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "status": "analysis_complete",

            "account": account,

            "market_context": context,

            "structure": structure,

            "price_action": price_action,

            "macd": macd,

            "strategy": strategy_result,

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

                "message": "Invalid direction"

            }


        if volume <= 0:

            return {

                "success": False,

                "message": "Invalid volume"

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

        if not order_id:

            return {

                "success": False,

                "message": "Invalid order id"

            }


        return self.orders.close_trade(
            order_id
        )


    def get_open_positions(self):

        positions = self.orders.get_open_positions()

        if positions is None:

            return []

        return positions


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

            "status": "rejected",

            "reason": reason,

            "account": account,

            "decision": "NO_TRADE"

        }
```

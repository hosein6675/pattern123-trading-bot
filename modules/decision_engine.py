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

        # ==========================================
        # 1. SYMBOL FILTER
        # ==========================================

        if not active_config.is_symbol_allowed(symbol):

            return {
                "symbol": symbol,
                "status": "symbol_not_allowed",
                "decision": "NO_TRADE"
            }

        # ==========================================
        # 2. MARKET DATA
        # ==========================================

        if not candles:

            candles_result = (
                self.market_data.get_candles(
                    symbol,
                    timeframe,
                    days=200
                )
            )

            if not candles_result:

                return {
                    "symbol": symbol,
                    "status": "market_data_error",
                    "decision": "NO_TRADE"
                }

            candles = candles_result.get(
                "candles",
                []
            )

        if not candles:

            return {
                "symbol": symbol,
                "status": "no_candles",
                "decision": "NO_TRADE"
            }

        # ==========================================
        # 3. NEWS FILTER
        # ==========================================

        news_status = self.news.check_news(
            symbol
        )

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
                "status": "trade_blocked_news",
                "decision": "NO_TRADE"
            }

        # ==========================================
        # 4. MARKET CONTEXT
        # ==========================================

        market_context = self.context.analyze(
            candles,
            symbol
        )

        # ==========================================
        # 5. STRUCTURE
        # ==========================================

        structure_result = self.structure.analyze(
            candles
        )

        # ==========================================
        # 6. PRICE ACTION
        # ==========================================

        pa_result = self.price_action.analyze(
            structure_result,
            candles
        )

        # ==========================================
        # 7. MACD
        # ==========================================

        macd_result = self.macd.analyze(
            candles
        )

        # ==========================================
        # 8. CURRENT OPEN POSITIONS
        # ==========================================

        open_positions = (
            self.orders.get_open_positions()
        )

        open_position_count = len(
            open_positions
        )

        # ==========================================
        # 9. INITIAL DECISION
        # ==========================================

        decision_result = self.decision.analyze(
            structure=structure_result,
            price_action=pa_result,
            macd=macd_result,
            market_context=market_context,
            news=news_status,
            risk=None
        )

        # ==========================================
        # 10. RISK CHECK
        # ==========================================

        entry = getattr(
            pa_result,
            "entry",
            0
        )

        stop_loss = getattr(
            pa_result,
            "stop_loss",
            0
        )

        quality = getattr(
            decision_result,
            "quality",
            0
        )

        risk_result = self.risk.check(
            balance=account.balance,
            entry=entry,
            stop_loss=stop_loss,
            quality=quality,
            loss_amount=0,
            open_positions=open_position_count
        )

        # ==========================================
        # 11. FINAL DECISION
        # ==========================================

        final_decision = self.decision.analyze(
            structure=structure_result,
            price_action=pa_result,
            macd=macd_result,
            market_context=market_context,
            news=news_status,
            risk=risk_result
        )

        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "status": "analysis_complete",

            "account": account,

            "news": news_status,

            "market_context": market_context,

            "structure": structure_result,

            "price_action": pa_result,

            "macd": macd_result,

            "risk": risk_result,

            "decision": final_decision,

            "open_positions": open_position_count
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
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def close_order(self, order_id):

        return self.orders.close_trade(
            order_id
        )

    def get_open_positions(self):

        return self.orders.get_open_positions()

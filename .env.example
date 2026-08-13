from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.journal import JournalEngine
from modules.account_manager import AccountManager
from modules.market_context import MarketContextAnalyzer



class TradingEngine:


    def __init__(self):

        self.context = MarketContextAnalyzer()

        self.structure = StructureAnalyzer()

        self.price_action = PriceActionEngine()

        self.macd = MACDEngine()

        self.risk = RiskManager()

        self.journal = JournalEngine()

        self.account = AccountManager()



    def analyze_market(self, symbol, timeframe, candles):


        # دریافت وضعیت حساب
        account = self.account.get_account()



        # بررسی شرایط کلی بازار قبل از سیگنال
        market_context = self.context.analyze(
            candles,
            symbol
        )



        # تحلیل ساختار بازار
        structure_result = self.structure.analyze(
            candles
        )



        # تحلیل پرایس اکشن
        pa_result = self.price_action.analyze(
            structure_result,
            candles
        )



        # تحلیل MACD
        macd_result = self.macd.analyze(
            candles
        )



        # مدیریت سرمایه
        risk_result = self.risk.check(

            balance=account.balance,

            loss_amount=0,

            position_size=0

        )



        return {

            "symbol": symbol,

            "timeframe": timeframe,

            "account": account,

            "market_context": market_context,

            "structure": structure_result,

            "price_action": pa_result,

            "macd": macd_result,

            "risk": risk_result

        }

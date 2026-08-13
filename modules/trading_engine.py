from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.journal import JournalEngine


class TradingEngine:

    def __init__(self):

        self.structure = StructureAnalyzer()
        self.price_action = PriceActionEngine()
        self.macd = MACDEngine()
        self.risk = RiskManager()
        self.journal = JournalEngine()


    def analyze_market(self, symbol, timeframe, candles):

        structure_result = self.structure.analyze(candles)

        pa_result = self.price_action.analyze(
            structure_result,
            candles
        )

        macd_result = self.macd.analyze(candles)

        risk_result = self.risk.check(
            0,
            0,
            0
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "structure": structure_result,
            "price_action": pa_result,
            "macd": macd_result,
            "risk": risk_result
        }

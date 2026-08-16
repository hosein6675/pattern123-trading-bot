
from modules.trading_engine import TradingEngine


engine = TradingEngine()

result = engine.analyze_market(
    symbol="XAUUSD",
    timeframe="H1"
)

print(result)

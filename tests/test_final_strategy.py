from modules.structure import StructureAnalyzer
from modules.trendline_fan import TrendlineFanAnalyzer
from modules.strategy_engine import StrategyEngine
from modules.price_action import EntrySignal
from modules.macd_engine import MACDResult
from modules.market_context import MarketContext


def candles_from_closes(closes):
    return [{"open": c - 0.2, "high": c + 0.5, "low": c - 0.5, "close": c} for c in closes]


def test_structure_produces_swings_and_direction():
    values = [100, 101, 102, 101, 100, 103, 104, 103, 102, 105, 106, 105,
              104, 107, 108, 107, 106, 109, 110, 109, 108, 111, 112, 111,
              110, 113, 114, 113, 112, 115]
    result = StructureAnalyzer().analyze(candles_from_closes(values))
    assert len(result.swing_highs) >= 2
    assert len(result.swing_lows) >= 2
    assert result.trend in {"bullish", "bearish", "range"}


def test_trendline_fan_returns_structured_result():
    candles = candles_from_closes([100 + i * 0.5 for i in range(30)])
    structure = StructureAnalyzer().analyze(candles)
    fan = TrendlineFanAnalyzer().analyze(structure, candles)
    assert fan.direction in {"buy", "sell", "none"}
    assert 0 <= fan.score <= 20


def test_strategy_requires_trendline_when_configured():
    structure = type("S", (), {"trend": "bullish", "structure_quality": 80})()
    price = EntrySignal("buy", 101, 99, 103, 105, 107, 90, 100, True, True, "ok")
    macd = MACDResult(True, False, False, True, 80, 1, 0.5, 0.5, "ok")
    context = MarketContext("EURUSD", "bullish", "bullish", "bullish", "no", "pending", "trend_continuation", "normal", "pending", "pending", "unknown", 80)
    fan = type("F", (), {"score": 20, "direction": "buy"})()
    result = StrategyEngine().evaluate(structure, price, macd, context, fan, "M15")
    assert result.direction == "buy"
    assert result.approved is True
    assert result.score >= 70


def test_strategy_rejects_direction_mismatch():
    structure = type("S", (), {"trend": "bullish", "structure_quality": 80})()
    price = EntrySignal("sell", 101, 103, 99, 97, 95, 90, 100, True, True, "ok")
    macd = MACDResult(True, False, False, True, 80, 1, 0.5, 0.5, "ok")
    context = MarketContext("EURUSD", "bullish", "bullish", "bullish", "no", "pending", "trend_continuation", "normal", "pending", "pending", "unknown", 80)
    fan = type("F", (), {"score": 0, "direction": "none"})()
    result = StrategyEngine().evaluate(structure, price, macd, context, fan, "M15")
    assert result.approved is False
    assert result.direction == "none"

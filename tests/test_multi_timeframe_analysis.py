from modules.multi_timeframe_analysis import analyze
from modules.telegram_controls import TelegramSelection


class FakeEngine:
    def __init__(self):
        self.calls = []

    def analyze_market(self, symbol, timeframe):
        self.calls.append((symbol, timeframe))
        return {"status": "analysis_complete", "symbol": symbol, "timeframe": timeframe}


def test_multi_timeframe_analysis_uses_selected_layers():
    engine = FakeEngine()
    selection = TelegramSelection(structure_timeframe="D1", analysis_timeframe="M5", trigger_timeframe="M1")
    result = analyze(engine, "EURUSD", selection)

    assert engine.calls == [("EURUSD", "D1"), ("EURUSD", "M5"), ("EURUSD", "M1")]
    assert result.status == "ready"
    assert result.warnings == ()


def test_multi_timeframe_analysis_reports_partial_data_without_fabricating():
    class PartialEngine(FakeEngine):
        def analyze_market(self, symbol, timeframe):
            self.calls.append((symbol, timeframe))
            if timeframe == "M1":
                return {"status": "rejected", "reason": "Market data unavailable"}
            return {"status": "analysis_complete"}

    result = analyze(PartialEngine(), "XAUUSD", TelegramSelection())
    assert result.status == "partial"
    assert any("تریگر M1" in warning for warning in result.warnings)

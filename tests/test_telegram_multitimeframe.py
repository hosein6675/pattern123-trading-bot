import asyncio

from modules.multi_timeframe_analysis import analyze
from modules.telegram_bot import TelegramBot
from modules.telegram_controls import TelegramSelection


class FakeEngine:
    def __init__(self):
        self.calls = []

    def analyze_market(self, symbol, timeframe):
        self.calls.append((symbol, timeframe))
        return {
            "status": "analysis_complete",
            "decision": {"decision": "NO_TRADE", "confidence": 50},
            "structure": {"trend": "neutral"},
            "strategy": {"reasons": [f"checked {timeframe}"], "warnings": []},
        }


def test_multi_timeframe_analysis_calls_all_selected_layers():
    engine = FakeEngine()
    selection = TelegramSelection(
        structure_timeframe="D1",
        analysis_timeframe="M15",
        trigger_timeframe="M1",
        symbols={"EURUSD"},
    )

    result = analyze(engine, "eurusd", selection)

    assert result.status == "ready"
    assert result.structure_timeframe == "D1"
    assert result.analysis_timeframe == "M15"
    assert result.trigger_timeframe == "M1"
    assert engine.calls == [
        ("EURUSD", "D1"),
        ("EURUSD", "M15"),
        ("EURUSD", "M1"),
    ]


def test_telegram_analysis_uses_multi_timeframe_pipeline():
    engine = FakeEngine()
    bot = TelegramBot("test-token", engine)
    selection = TelegramSelection(
        structure_timeframe="H4",
        analysis_timeframe="M5",
        trigger_timeframe="M1",
        symbols={"EURUSD"},
    )

    text = asyncio.run(bot._analysis_text(selection))

    assert "🏗 ساختار" in text
    assert "🔎 تحلیل" in text
    assert "🎯 تریگر" in text
    assert engine.calls == [
        ("EURUSD", "H4"),
        ("EURUSD", "M5"),
        ("EURUSD", "M1"),
    ]

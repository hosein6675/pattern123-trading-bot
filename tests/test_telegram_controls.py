import pytest

from modules.telegram_controls import (
    ANALYSIS_TIMEFRAMES,
    STRUCTURE_TIMEFRAMES,
    TRIGGER_TIMEFRAMES,
    TelegramSelection,
    analysis_view_from_result,
    render_analysis,
)


def test_timeframe_groups_match_operational_design():
    assert STRUCTURE_TIMEFRAMES == ("D1", "H4", "H1")
    assert ANALYSIS_TIMEFRAMES == ("H1", "M15", "M5", "M1")
    assert TRIGGER_TIMEFRAMES == ("M15", "M5", "M1")


def test_selection_can_change_all_three_timeframe_layers():
    selection = TelegramSelection()
    selection.set_structure_timeframe("D1")
    selection.set_analysis_timeframe("M5")
    selection.set_trigger_timeframe("M15")
    assert (selection.structure_timeframe, selection.analysis_timeframe, selection.trigger_timeframe) == ("D1", "M5", "M15")


def test_invalid_timeframes_are_rejected():
    selection = TelegramSelection()
    with pytest.raises(ValueError):
        selection.set_structure_timeframe("M5")
    with pytest.raises(ValueError):
        selection.set_analysis_timeframe("D1")
    with pytest.raises(ValueError):
        selection.set_trigger_timeframe("H4")


def test_symbols_support_multiple_selection_and_toggle():
    selection = TelegramSelection(symbols={"EURUSD"})
    allowed = {"EURUSD", "GBPUSD", "XAUUSD"}
    assert selection.toggle_symbol("GBPUSD", allowed) is True
    assert selection.symbols == {"EURUSD", "GBPUSD"}
    assert selection.toggle_symbol("GBPUSD", allowed) is False
    assert selection.symbols == {"EURUSD"}


def test_empty_symbol_set_requires_explicit_non_empty_set():
    selection = TelegramSelection()
    with pytest.raises(ValueError, match="at least one symbol"):
        selection.set_symbols([], {"EURUSD"})


def test_analysis_view_exposes_structure_trendline_and_zone_fields():
    selection = TelegramSelection(structure_timeframe="H4", analysis_timeframe="M15", trigger_timeframe="M1", symbols={"EURUSD"})
    result = {
        "status": "analysis_complete",
        "market_context": {"structure": "bullish", "fib_zone": "discount", "zone_authenticity": "confirmed", "price_position": "inside"},
        "structure": {"trend": "bullish"},
        "trendline_fan": {"direction": "bullish"},
        "decision": {"decision": "BUY", "confidence": 82, "reasons": ["structure aligned"], "warnings": []},
    }
    view = analysis_view_from_result(result, symbol="EURUSD", selection=selection)
    text = render_analysis(view)
    assert "EURUSD" in text
    assert "H4" in text and "M15" in text and "M1" in text
    assert "bullish" in text
    assert "discount" in text
    assert "confirmed" in text
    assert "82%" in text

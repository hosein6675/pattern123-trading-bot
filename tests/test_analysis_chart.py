from modules.analysis_chart import build_analysis_chart


def test_analysis_chart_renders_mt5_observation_fixture():
    candles = []
    for i in range(30):
        base = 100.0 + i * 0.1
        candles.append({
            "time": 1_700_000_000 + i * 60,
            "open": base,
            "high": base + 0.2,
            "low": base - 0.1,
            "close": base + 0.1,
            "volume": 10,
        })

    result = {
        "symbol": "TEST",
        "timeframe": "M15",
        "structure_timeframe": "H4",
        "trigger_timeframe": "M1",
        "decision": "NO_TRADE",
        "chart_candles": candles,
        "structure": {
            "trend": "bullish",
            "swing_lows": [{"index": 8, "price": 100.7}, {"index": 20, "price": 101.9}],
            "swing_highs": [{"index": 14, "price": 101.5}, {"index": 25, "price": 102.7}],
        },
        "trendline_fan": {"support_slope": 0.1, "resistance_slope": 0.1},
        "price_action": {"entry": 102.9, "stop_loss": 101.9, "tp1": 103.9, "tp2": 104.9, "tp3": 105.9},
        "trigger": {"status": "NO_TRADE"},
    }

    image = build_analysis_chart(result)

    assert image.startswith(b"\x89PNG")
    assert len(image) > 10_000

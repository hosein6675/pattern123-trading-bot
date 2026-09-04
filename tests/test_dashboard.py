from modules.dashboard import render


def test_dashboard_renders_snapshot():
    page = render({
        "status": "analysis_complete",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "mode": "demo",
        "broker_connected": False,
        "account": {"equity": 10000},
        "risk": {
            "risk_percent": 0.5,
            "daily_drawdown": 1.2,
            "account_drawdown": 2.0,
            "total_risk_percent": 1.5,
            "consecutive_losses": 1,
        },
        "decision": {"decision": "BUY", "direction": "buy", "confidence": 88},
        "strategy": {
            "score": 90,
            "confidence": 95,
            "direction": "buy",
            "entry": 100.0,
            "stop_loss": 95.0,
            "tp1": 105.0,
            "tp2": 110.0,
            "tp3": 115.0,
            "risk_reward": 3.0,
            "reasons": ["Pattern123 price action confirmed", "MACD confirms trade direction"],
            "warnings": [],
        },
        "macd": {"score": 80, "histogram": 1.5},
        "trendline_fan": {"direction": "buy", "score": 20},
        "market_context": {"trend": "bullish"},
        "structure": {"trend": "bullish", "structure_quality": 85},
        "open_positions": 1,
    })
    assert "Pattern123 Trading Dashboard" in page
    assert "EURUSD" in page
    assert "BUY" in page
    assert "Execution levels" in page
    assert "Risk/reward" not in page
    assert "115.0" in page
    assert "MACD confirms trade direction" in page
    assert "Broker connected" in page

from modules.dashboard import render


def test_dashboard_renders_snapshot():
    page = render({
        "status": "strategy_rejected",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "account": {"equity": 10000},
        "risk": {"risk_percent": 0.5},
        "decision": {"decision": "NO_TRADE", "direction": "none"},
        "strategy": {"score": 65},
        "macd": {"score": 40},
        "market_context": {"trend": "bullish"},
        "open_positions": 1,
    })
    assert "Pattern123 Trading Dashboard" in page
    assert "EURUSD" in page
    assert "NO_TRADE" in page

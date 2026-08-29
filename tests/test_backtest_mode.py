from datetime import datetime, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.mode import BacktestMode, context_for


def test_each_mode_exposes_only_selected_context():
    snapshot = BacktestSnapshot(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        100.0,
        {"pattern": "123"},
        news_data=("news",),
        order_flow_data=("delta",),
    )

    assert context_for(snapshot, BacktestMode.PATTERN_ONLY) == {"pattern": {"pattern": "123"}}
    assert context_for(snapshot, BacktestMode.NEWS_ONLY) == {"news": ("news",)}
    assert context_for(snapshot, BacktestMode.ORDER_FLOW_ONLY) == {"order_flow": ("delta",)}
    assert context_for(snapshot, BacktestMode.COMBINED) == {
        "pattern": {"pattern": "123"},
        "news": ("news",),
        "order_flow": ("delta",),
    }

from datetime import datetime, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.matrix import run_mode_matrix
from backtest.mode import BacktestMode


def test_mode_matrix_runs_each_mode_independently():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    snapshot = BacktestSnapshot(ts, 100.0, {"decision": "long"}, ("news",), ("delta",))

    def factory(mode):
        def strategy(item):
            return (
                item.pattern_data,
                item.news_data,
                item.order_flow_data,
            )
        return strategy

    results = run_mode_matrix([snapshot], factory)
    assert [item.mode for item in results] == list(BacktestMode)
    assert results[0].result.decisions == (({"decision": "long"}, (), ()),)
    assert results[1].result.decisions == (({}, ("news",), ()),)
    assert results[2].result.decisions == (({}, (), ("delta",)),)
    assert results[3].result.decisions == (({"decision": "long"}, ("news",), ("delta",)),)

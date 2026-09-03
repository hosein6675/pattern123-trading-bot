from backtest.matrix import ModeResult
from backtest.report import build_report
from backtest.runner import BacktestResult
from backtest.mode import BacktestMode


def test_report_preserves_mode_and_run_counts():
    results = [
        ModeResult(BacktestMode.PATTERN_ONLY, BacktestResult(("long", "flat"), 2)),
        ModeResult(BacktestMode.ORDER_FLOW_ONLY, BacktestResult(("short",), 1)),
    ]
    report = build_report(results)
    assert report[0].mode == "pattern_only"
    assert report[0].snapshots == 2
    assert report[0].decisions == 2
    assert report[1].mode == "order_flow_only"
    assert report[1].snapshots == 1
    assert report[1].decisions == 1

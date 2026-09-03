from backtest.matrix import ModeResult
from backtest.mode import BacktestMode
from backtest.report import build_report
from backtest.runner import BacktestResult


def test_report_calculates_real_metrics_from_numeric_pnl():
    result = ModeResult(
        BacktestMode.PATTERN_ONLY,
        BacktestResult((10.0, -5.0, 15.0, -10.0, "long"), 5),
    )
    report = build_report([result])[0]
    assert report.win_rate == 0.5
    assert report.profit_factor == 25.0 / 15.0
    assert report.max_drawdown == 10.0


def test_report_handles_no_numeric_pnl_without_fabrication():
    result = ModeResult(
        BacktestMode.NEWS_ONLY,
        BacktestResult(("bullish", "bearish"), 2),
    )
    report = build_report([result])[0]
    assert report.win_rate == 0.0
    assert report.profit_factor == 0.0
    assert report.max_drawdown == 0.0

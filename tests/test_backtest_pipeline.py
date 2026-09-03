from datetime import datetime, timezone

from backtest.pipeline import run_csv_report
from backtest.mode import BacktestMode


def test_csv_pipeline_runs_all_modes_and_reports(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text(
        "timestamp,price\n"
        "2026-01-01T00:00:00+00:00,100\n"
        "2026-01-01T00:01:00+00:00,101\n",
        encoding="utf-8",
    )

    def factory(mode):
        def strategy(snapshot):
            if mode is BacktestMode.PATTERN_ONLY:
                assert snapshot.news_data == () and snapshot.order_flow_data == ()
            elif mode is BacktestMode.NEWS_ONLY:
                assert snapshot.pattern_data == {} and snapshot.order_flow_data == ()
            elif mode is BacktestMode.ORDER_FLOW_ONLY:
                assert snapshot.pattern_data == {} and snapshot.news_data == ()
            else:
                assert snapshot.pattern_data and snapshot.news_data == () and snapshot.order_flow_data == ()
            return 1.0 if mode is not BacktestMode.NEWS_ONLY else -1.0
        return strategy

    reports = run_csv_report(
        str(path),
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        factory,
    )
    assert [report.mode for report in reports] == [mode.value for mode in BacktestMode]
    assert all(report.snapshots == 2 for report in reports)
    assert reports[0].win_rate == 1.0
    assert reports[1].win_rate == 0.0

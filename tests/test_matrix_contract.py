from datetime import datetime, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.matrix import run_mode_matrix
from backtest.mode import BacktestMode


def test_mode_matrix_passes_full_snapshot_to_strategy():
    snapshot = BacktestSnapshot(datetime(2026, 1, 1, tzinfo=timezone.utc), 100.0, {"x": 1})
    seen = []

    def factory(_mode):
        return lambda value: seen.append(value) or 1.0

    results = run_mode_matrix((snapshot,), factory, (BacktestMode.PATTERN_ONLY,))
    assert len(results) == 1
    assert seen == [snapshot]

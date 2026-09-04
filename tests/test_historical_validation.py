from datetime import datetime, timezone
from pathlib import Path

import pytest

from backtest.historical_validation import (
    load_historical_dataset,
    run_csv_validation,
    snapshots_from_ohlc,
)
from backtest.mode import BacktestMode
from backtest.validation_lab import TradeObservation, ValidationThresholds
from modules.market_intelligence.backtest.execution import ExecutionCosts


CSV = (
    "timestamp,open,high,low,close,volume\n"
    "2026-01-01T00:00:00+00:00,100,105,99,103,10\n"
    "2026-01-01T00:01:00+00:00,103,106,102,105,12\n"
    "2026-01-01T00:02:00+00:00,105,108,104,107,14\n"
    "2026-01-01T00:03:00+00:00,107,109,106,108,16\n"
    "2026-01-01T00:04:00+00:00,108,110,107,109,18\n"
    "2026-01-01T00:05:00+00:00,109,111,108,110,20\n"
)


def test_load_historical_dataset_applies_half_open_window(tmp_path: Path):
    path = tmp_path / "prices.csv"
    path.write_text(CSV, encoding="utf-8")
    dataset = load_historical_dataset(
        path,
        symbol="EURUSD",
        timeframe="m15",
        start=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 0, 4, tzinfo=timezone.utc),
    )
    assert dataset.symbol == "EURUSD"
    assert dataset.timeframe == "M15"
    assert dataset.row_count == 3
    assert dataset.records[0].timestamp.hour == 0
    assert dataset.records[0].timestamp.minute == 1
    assert dataset.records[-1].timestamp.minute == 3


def test_snapshot_conversion_preserves_ohlc_as_point_in_time_data(tmp_path: Path):
    path = tmp_path / "prices.csv"
    path.write_text(CSV, encoding="utf-8")
    dataset = load_historical_dataset(
        path,
        symbol="EURUSD",
        timeframe="M15",
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 0, 6, tzinfo=timezone.utc),
    )
    snapshots = snapshots_from_ohlc(dataset.records)
    assert snapshots[0].price == 103
    assert snapshots[0].pattern_data["open"] == 100
    assert snapshots[-1].pattern_data["close"] == 110


def test_run_csv_validation_requires_explicit_execution_costs(tmp_path: Path):
    path = tmp_path / "prices.csv"
    path.write_text(CSV, encoding="utf-8")
    dataset = load_historical_dataset(
        path,
        symbol="EURUSD",
        timeframe="M15",
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 0, 6, tzinfo=timezone.utc),
    )

    def factory(_mode):
        return lambda _snapshot: 1.0

    def extract(decision, snapshot):
        return TradeObservation(pnl=decision, timestamp=snapshot.timestamp)

    with pytest.raises(ValueError, match="execution costs"):
        run_csv_validation(
            dataset,
            strategy_factory=factory,
            outcome_extractor=extract,
            modes=(BacktestMode.PATTERN_ONLY,),
            train_size=2,
            test_size=2,
            costs=None,  # type: ignore[arg-type]
        )


def test_run_csv_validation_wires_real_csv_contract_into_lab(tmp_path: Path):
    path = tmp_path / "prices.csv"
    path.write_text(CSV, encoding="utf-8")
    dataset = load_historical_dataset(
        path,
        symbol="EURUSD",
        timeframe="M15",
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 0, 6, tzinfo=timezone.utc),
    )

    def factory(_mode):
        return lambda _snapshot: 2.0

    def extract(decision, snapshot):
        return TradeObservation(pnl=decision, timestamp=snapshot.timestamp)

    result = run_csv_validation(
        dataset,
        strategy_factory=factory,
        outcome_extractor=extract,
        modes=(BacktestMode.PATTERN_ONLY,),
        train_size=2,
        test_size=2,
        costs=ExecutionCosts(spread=0.5),
        thresholds=ValidationThresholds(minimum_oos_trades=1),
    )
    assert result.modes[0].out_of_sample.trades == 4
    assert result.modes[0].out_of_sample.net_pnl == 6.0

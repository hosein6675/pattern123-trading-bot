"""End-to-end historical CSV validation wiring with explicit outcome extraction."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.market_intelligence.backtest.execution import ExecutionCosts, ExecutionModel

from .data_snapshot import BacktestSnapshot
from .mode import BacktestMode
from .ohlc_csv import OHLCRecord, load_ohlc_csv
from .validation_lab import (
    TradeObservation,
    ValidationLabResult,
    ValidationThresholds,
    run_validation_lab,
)


@dataclass(frozen=True, slots=True)
class HistoricalDataset:
    path: Path
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    records: tuple[OHLCRecord, ...]

    @property
    def row_count(self) -> int:
        return len(self.records)


StrategyFactory = Callable[[BacktestMode], Callable[[BacktestSnapshot], Any]]
OutcomeExtractor = Callable[[Any, BacktestSnapshot], TradeObservation | None]


def load_historical_dataset(
    path: str | Path,
    *,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> HistoricalDataset:
    """Load one real OHLC CSV and apply an explicit half-open time window."""
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("start must be timezone-aware")
    if end.tzinfo is None or end.utcoffset() is None:
        raise ValueError("end must be timezone-aware")
    if end <= start:
        raise ValueError("end must be after start")
    if not symbol.strip() or not timeframe.strip():
        raise ValueError("symbol and timeframe are required")

    records = tuple(
        record
        for record in load_ohlc_csv(path)
        if start <= record.timestamp < end
    )
    if not records:
        raise ValueError("historical dataset contains no rows in the requested window")

    return HistoricalDataset(
        path=Path(path),
        symbol=symbol.strip(),
        timeframe=timeframe.strip().upper(),
        start=start,
        end=end,
        records=records,
    )


def snapshots_from_ohlc(records: Sequence[OHLCRecord]) -> tuple[BacktestSnapshot, ...]:
    """Convert validated OHLC records to immutable point-in-time snapshots."""
    return tuple(
        BacktestSnapshot(
            timestamp=record.timestamp,
            price=record.close,
            pattern_data={
                "open": record.open,
                "high": record.high,
                "low": record.low,
                "close": record.close,
                "volume": record.volume,
            },
        )
        for record in records
    )


def run_csv_validation(
    dataset: HistoricalDataset,
    *,
    strategy_factory: StrategyFactory,
    outcome_extractor: OutcomeExtractor,
    modes: Sequence[BacktestMode],
    train_size: int,
    test_size: int,
    costs: ExecutionCosts,
    execution_model: ExecutionModel | None = None,
    step: int | None = None,
    thresholds: ValidationThresholds = ValidationThresholds(),
) -> ValidationLabResult:
    """Run leakage-resistant validation with execution costs explicitly required."""
    if costs is None:
        raise ValueError("execution costs must be explicitly supplied")
    snapshots = snapshots_from_ohlc(dataset.records)
    return run_validation_lab(
        snapshots,
        strategy_factory,
        outcome_extractor,
        modes,
        train_size,
        test_size,
        step=step,
        execution_model=execution_model,
        costs=costs,
        thresholds=thresholds,
    )

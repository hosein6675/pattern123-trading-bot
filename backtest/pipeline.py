"""Reference pipeline for historical replay without strategy/data coupling."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from .csv_adapter import CsvPriceAdapter
from .data_snapshot import BacktestSnapshot
from .matrix import ModeResult, StrategyFactory, run_mode_matrix
from .mode import BacktestMode
from .report import ModeReport, build_report


def run_csv_backtest(
    path: str,
    start: datetime,
    end: datetime,
    strategy_factory: StrategyFactory,
    modes: tuple[BacktestMode, ...] = tuple(BacktestMode),
) -> tuple[ModeResult, ...]:
    """Load point-in-time prices, create snapshots, and run isolated modes."""
    adapter = CsvPriceAdapter(path)
    snapshots = tuple(
        BacktestSnapshot(row.timestamp, row.price, {"price": row.price})
        for row in adapter.load(start, end)
    )
    return run_mode_matrix(snapshots, strategy_factory, modes)


def run_csv_report(
    path: str,
    start: datetime,
    end: datetime,
    strategy_factory: StrategyFactory,
    modes: tuple[BacktestMode, ...] = tuple(BacktestMode),
) -> tuple[ModeReport, ...]:
    return build_report(run_csv_backtest(path, start, end, strategy_factory, modes))

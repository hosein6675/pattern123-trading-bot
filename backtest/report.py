"""Comparison report for isolated backtest mode results."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .matrix import ModeResult
from .metrics import max_drawdown, profit_factor, win_rate


@dataclass(frozen=True, slots=True)
class ModeReport:
    mode: str
    snapshots: int
    decisions: int
    win_rate: float
    profit_factor: float
    max_drawdown: float


def build_report(results: Iterable[ModeResult]) -> tuple[ModeReport, ...]:
    reports: list[ModeReport] = []
    for item in results:
        numeric = tuple(
            value
            for value in item.result.decisions
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        )
        reports.append(
            ModeReport(
                mode=item.mode.value,
                snapshots=item.result.snapshots_processed,
                decisions=len(item.result.decisions),
                win_rate=win_rate(numeric),
                profit_factor=profit_factor(numeric),
                max_drawdown=max_drawdown(numeric),
            )
        )
    return tuple(reports)

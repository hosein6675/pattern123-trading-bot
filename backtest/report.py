"""Comparison report for isolated backtest mode results."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from .matrix import ModeResult


@dataclass(frozen=True, slots=True)
class ModeReport:
    mode: str
    snapshots: int
    decisions: int
    win_rate: float
    profit_factor: float
    max_drawdown: float


def build_report(results: Iterable[ModeResult]) -> tuple[ModeReport, ...]:
    reports = []
    for item in results:
        decisions = item.result.decisions
        reports.append(
            ModeReport(
                mode=item.mode.value,
                snapshots=item.result.snapshots_processed,
                decisions=len(decisions),
                win_rate=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
            )
        )
    return tuple(reports)

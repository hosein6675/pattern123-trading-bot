"""Comparison report for isolated backtest mode results."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import inf

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
        values = tuple(item.result.decisions)
        numeric = tuple(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
        gross_profit = sum(v for v in numeric if v > 0)
        gross_loss = -sum(v for v in numeric if v < 0)
        wins = sum(v > 0 for v in numeric)
        equity = peak = drawdown = 0.0
        for value in numeric:
            equity += value
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        profit_factor = inf if gross_loss == 0 and gross_profit > 0 else (gross_profit / gross_loss if gross_loss else 0.0)
        reports.append(ModeReport(item.mode.value, item.result.snapshots_processed, len(values), wins / len(numeric) if numeric else 0.0, profit_factor, drawdown))
    return tuple(reports)

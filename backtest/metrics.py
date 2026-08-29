"""Pure performance metrics for comparing backtest mode outputs."""

from __future__ import annotations

from math import inf
from collections.abc import Iterable


def win_rate(returns: Iterable[float]) -> float:
    values = tuple(returns)
    return sum(value > 0 for value in values) / len(values) if values else 0.0


def profit_factor(returns: Iterable[float]) -> float:
    values = tuple(returns)
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return inf if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def max_drawdown(equity_changes: Iterable[float]) -> float:
    peak = 0.0
    equity = 0.0
    drawdown = 0.0
    for change in equity_changes:
        equity += change
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown

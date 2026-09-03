from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DataMode(str, Enum):
    BASELINE = "baseline"
    OBSERVE = "observe"
    ORDER_FLOW = "order_flow"


@dataclass(frozen=True)
class BacktestConfig:
    mode: DataMode = DataMode.BASELINE
    starting_balance: float = 10_000.0
    risk_per_trade_pct: float = 1.0


@dataclass(frozen=True)
class TradeResult:
    pnl: float
    won: bool


@dataclass(frozen=True)
class BacktestMetrics:
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    net_pnl: float
    max_drawdown: float

    @classmethod
    def from_results(cls, results: list[TradeResult]) -> "BacktestMetrics":
        if not results:
            return cls(0, 0, 0, 0.0, 0.0, 0.0)
        wins = sum(r.won for r in results)
        losses = len(results) - wins
        equity = peak = 0.0
        max_dd = 0.0
        for result in results:
            equity += result.pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return cls(
            trades=len(results),
            wins=wins,
            losses=losses,
            win_rate_pct=(wins / len(results)) * 100.0,
            net_pnl=sum(r.pnl for r in results),
            max_drawdown=max_dd,
        )


@dataclass(frozen=True)
class BacktestComparison:
    baseline: BacktestMetrics
    order_flow: Optional[BacktestMetrics] = None

    @property
    def win_rate_delta_pct(self) -> Optional[float]:
        if self.order_flow is None:
            return None
        return self.order_flow.win_rate_pct - self.baseline.win_rate_pct

    @property
    def pnl_delta(self) -> Optional[float]:
        if self.order_flow is None:
            return None
        return self.order_flow.net_pnl - self.baseline.net_pnl

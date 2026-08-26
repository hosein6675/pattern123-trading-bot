from __future__ import annotations

from collections.abc import Callable, Iterable

from .models import BacktestComparison, BacktestMetrics, DataMode, TradeResult


StrategyFn = Callable[[object, DataMode], TradeResult | None]


class BacktestEngine:
    """Run the same dataset under isolated data modes for controlled A/B tests."""

    def run(
        self,
        candles: Iterable[object],
        strategy: StrategyFn,
        mode: DataMode = DataMode.BASELINE,
    ) -> BacktestMetrics:
        results: list[TradeResult] = []
        for candle in candles:
            result = strategy(candle, mode)
            if result is not None:
                results.append(result)
        return BacktestMetrics.from_results(results)

    def compare(
        self,
        candles: list[object],
        strategy: StrategyFn,
    ) -> BacktestComparison:
        baseline = self.run(candles, strategy, DataMode.BASELINE)
        order_flow = self.run(candles, strategy, DataMode.ORDER_FLOW)
        return BacktestComparison(baseline=baseline, order_flow=order_flow)

from modules.market_intelligence.backtest.engine import BacktestEngine
from modules.market_intelligence.backtest.models import DataMode, TradeResult


def test_metrics_are_computed_without_order_flow_assumptions():
    def strategy(candle, mode):
        assert mode is DataMode.BASELINE
        return candle

    results = [TradeResult(10, True), TradeResult(-5, False), TradeResult(15, True)]
    metrics = BacktestEngine().run(results, strategy, DataMode.BASELINE)

    assert metrics.trades == 3
    assert metrics.wins == 2
    assert metrics.losses == 1
    assert metrics.win_rate_pct == 100 * 2 / 3
    assert metrics.net_pnl == 20
    assert metrics.max_drawdown == 5


def test_compare_uses_identical_input_for_both_modes():
    calls = []

    def strategy(candle, mode):
        calls.append(mode)
        return TradeResult(candle, candle > 0)

    candles = [10, -5, 20]
    comparison = BacktestEngine().compare(candles, strategy)

    assert comparison.baseline.trades == 3
    assert comparison.order_flow is not None
    assert comparison.order_flow.trades == 3
    assert comparison.pnl_delta == 0
    assert calls == [DataMode.BASELINE] * 3 + [DataMode.ORDER_FLOW] * 3

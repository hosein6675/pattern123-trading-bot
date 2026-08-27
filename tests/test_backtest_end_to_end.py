from datetime import datetime, timedelta, timezone

from modules.market_intelligence.backtest.adapters import ReplayAdapter
from modules.market_intelligence.backtest.engine import BacktestEngine
from modules.market_intelligence.backtest.execution import ExecutionCosts, ExecutionModel
from modules.market_intelligence.backtest.models import DataMode, TradeResult
from modules.market_intelligence.backtest.replay import HistoricalReplay


def test_replay_adapter_engine_execution_end_to_end():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = [
        {"ts": base + timedelta(minutes=2), "pnl": 8.0},
        {"ts": base + timedelta(minutes=1), "pnl": -3.0},
        {"ts": base + timedelta(minutes=3), "pnl": 5.0},
    ]

    replay_events = list(ReplayAdapter("test", records).events(lambda r: r["ts"]))
    replay = HistoricalReplay(replay_events)
    ordered = []
    assert replay.run(lambda event: ordered.append(event.payload["ts"])) == 3
    assert ordered == sorted(ordered)

    def strategy(record, mode):
        assert mode in (DataMode.BASELINE, DataMode.ORDER_FLOW)
        return TradeResult(record["pnl"], record["pnl"] > 0)

    candles = [event.payload for event in replay.events()]
    comparison = BacktestEngine().compare(candles, strategy)
    costs = ExecutionCosts(spread=0.5, slippage=0.25, commission=0.25)
    net = ExecutionModel().net_pnl(comparison.baseline.net_pnl, costs)

    assert comparison.baseline.trades == 3
    assert comparison.order_flow is not None
    assert comparison.order_flow.trades == 3
    assert net == 9.0

from datetime import datetime, timezone

from backtest.data_snapshot import BacktestSnapshot
from backtest.runner import BacktestRunner
from modules.market_intelligence.news.models import NewsBias, NewsSignal
from modules.market_intelligence.order_flow.models import OrderFlowSnapshot


UTC = timezone.utc


def test_market_intelligence_is_observation_only():
    ts = datetime(2026, 1, 9, 13, 20, tzinfo=UTC)
    news = NewsSignal("nfp", ts, NewsBias.BEARISH, 0.9, 2)
    flow = OrderFlowSnapshot(
        provider="cme-test",
        instrument="ES",
        timestamp=ts,
        bid=100.0,
        ask=100.25,
        bid_size=10,
        ask_size=8,
        delta=2,
        cumulative_delta=12,
        volume=18,
    )
    snapshot = BacktestSnapshot(
        timestamp=ts,
        price=100.0,
        pattern_data={"pattern": "123", "decision": "long"},
        news_data=(news,),
        order_flow_data=(flow,),
    )

    def pattern_only_strategy(item):
        return item.pattern_data["decision"]

    result = BacktestRunner(pattern_only_strategy).run([snapshot], as_of=ts)
    assert result.decisions == ("long",)
    assert result.snapshots_processed == 1
    assert snapshot.news_data == (news,)
    assert snapshot.order_flow_data == (flow,)

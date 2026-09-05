from modules.journal import JournalEngine


def test_mt5_trade_lifecycle_correlation(tmp_path):
    journal = JournalEngine(tmp_path / "journal.sqlite3")
    trade = journal.create_trade(
        symbol="EURUSD",
        timeframe="M1",
        direction="buy",
        entry_price=1.1000,
        stop_loss=1.0990,
        take_profit=1.1020,
        broker_order_id="1001",
        broker_deal_id="2001",
        broker_position_id="3001",
    )

    assert journal.find_by_broker_order("1001").trade_id == trade.trade_id
    assert journal.find_by_broker_deal("2001").trade_id == trade.trade_id
    assert journal.find_by_broker_position("3001").trade_id == trade.trade_id

    closed = journal.update_trade(
        trade.trade_id,
        exit_price=1.1020,
        exit_time="2026-09-05T20:00:00+00:00",
        result="CLOSED",
        profit_loss=20.0,
    )
    assert closed is not None
    assert closed.result == "CLOSED"
    assert closed.profit_loss == 20.0

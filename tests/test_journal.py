import tempfile

from modules.journal import JournalEngine
from modules.performance import PerformanceEngine


def test_lifecycle_and_events():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        journal = JournalEngine(f.name)
        trade_id = journal.record_trade_open(
            symbol="EURUSD",
            direction="buy",
            timeframe="M15",
            entry_price=1.1,
            volume=0.2,
            stop_loss=1.09,
            take_profit=1.12,
            risk_reward=2,
            risk_percent=1,
            risk_amount=10,
            entry_reason="strategy_confirmed",
            entry_snapshot={"source": "mt5"},
        )
        journal.record_event(
            trade_id,
            "stop_move",
            price=1.105,
            old_value={"sl": 1.09},
            new_value={"sl": 1.10},
            reason="break_even",
            actor="strategy",
        )
        assert journal.record_trade_close(
            trade_id,
            exit_price=1.11,
            net_pnl=20,
            gross_pnl=22,
            commission=2,
            exit_reason="strategy_exit",
            exit_snapshot={"source": "mt5"},
            mae_r=-0.3,
            mfe_r=1.4,
        )
        assert journal.get_trade(trade_id)["status"] == "closed"
        assert len(journal.get_events(trade_id)) == 2


def test_equity_and_summary_use_only_observed_snapshots():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        journal = JournalEngine(f.name)
        journal.record_account_snapshot(1000, 1000)
        journal.record_account_snapshot(
            1010, 1005, peak_equity=1010, drawdown_percent=0.5
        )
        journal.record_account_snapshot(
            1005, 995, peak_equity=1010, drawdown_percent=1.5
        )
        curve = PerformanceEngine.equity_curve(journal.get_account_snapshots())
        assert [x["equity"] for x in curve] == [1000, 1005, 995]
        summary = PerformanceEngine.summarize(
            journal.get_history(), journal.get_account_snapshots()
        )
        assert summary.initial_balance == 1000
        assert summary.current_balance == 1005
        assert summary.max_drawdown_percent == 1.5


def test_non_mt5_snapshot_rejected():
    journal = JournalEngine()
    try:
        journal.record_account_snapshot(1000, 1000, source="demo")
    except ValueError:
        pass
    else:
        raise AssertionError("non-MT5 data must be rejected")

from modules.distribution_manager import Destination, DistributionManager, ReportLevel
from modules.journal import JournalEngine
from modules.journal_analytics import analyze
from modules.system_control import SystemControl, SystemMode


def test_journal_persists_and_updates(tmp_path):
    journal = JournalEngine(tmp_path / "journal.sqlite3")
    trade = journal.create_trade("EURUSD", "M15", "buy", 1.1, stop_loss=1.09, take_profit=1.12)
    assert trade.trade_id
    assert journal.count() == 1
    journal.update_trade(trade.trade_id, exit_price=1.12, result="TP_HIT", profit_loss=12.5)
    restored = JournalEngine(tmp_path / "journal.sqlite3")
    item = restored.get_trade(trade.trade_id)
    assert item is not None
    assert item.result == "TP_HIT"
    assert item.exit_price == 1.12


def test_analytics_detects_repeated_factors(tmp_path):
    journal = JournalEngine(tmp_path / "journal.sqlite3")
    for _ in range(3):
        journal.create_trade("EURUSD", "M15", "buy", 1.1, 1.12, 1.09, 1.12, "TP_HIT", 10, positive_factors=["clean_breakout"])
    for _ in range(2):
        journal.create_trade("GBPUSD", "H1", "sell", 1.3, 1.31, 1.32, 1.28, "SL_HIT", -10, mistakes=["late_entry"])
    result = analyze(journal.get_history())
    assert result.closed == 5
    assert result.wins == 3
    assert result.losses == 2
    assert result.repeated_successes[0][0] == "clean_breakout"
    assert result.repeated_mistakes[0][0] == "late_entry"


def test_distribution_blocks_sensitive_public_destination():
    manager = DistributionManager()
    manager.register(Destination("public", "Public", "channel", ReportLevel.PUBLIC))
    manager.register(Destination("private", "Private", "user", ReportLevel.SENSITIVE))
    assert manager.can_deliver("public", sensitive=False)
    assert not manager.can_deliver("public", sensitive=True)
    assert manager.can_deliver("private", sensitive=True)


def test_system_control_is_fail_closed_until_auto_mode():
    control = SystemControl()
    assert not control.can_open_trade()
    control.set_mode(SystemMode.AUTO_TRADING)
    assert control.can_open_trade()
    control.activate_emergency_stop()
    assert not control.can_open_trade()

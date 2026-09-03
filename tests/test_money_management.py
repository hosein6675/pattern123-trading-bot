from modules.money_management import MoneyManagement
from modules.risk_manager import RiskManager


def test_broker_aware_position_size_uses_cash_risk_per_lot():
    manager = RiskManager()
    result = manager.check(
        balance=1000,
        entry=1.1000,
        stop_loss=1.0900,
        quality=95,
        risk_per_lot=100,
    )

    assert result.allowed is True
    assert result.risk_amount == 10.0
    assert result.lot_size == 0.1


def test_daily_drawdown_blocks_new_risk():
    manager = RiskManager()
    manager.check(1000, entry=1.1, stop_loss=1.09, quality=95, risk_per_lot=100)
    manager.register_loss(50)

    result = manager.check(
        1000,
        entry=1.1,
        stop_loss=1.09,
        quality=95,
        risk_per_lot=100,
    )

    assert result.allowed is False
    assert result.daily_drawdown == 5.0
    assert result.message == "Daily drawdown limit reached"


def test_consecutive_loss_guard_blocks_after_three_losses():
    manager = RiskManager()
    for _ in range(3):
        manager.register_trade_result(-1)

    result = manager.check(
        1000,
        entry=1.1,
        stop_loss=1.09,
        quality=95,
        risk_per_lot=100,
    )

    assert result.allowed is False
    assert result.consecutive_losses == 3
    assert result.message == "Maximum consecutive losses reached"


def test_total_risk_guard_blocks_portfolio_overallocation():
    manager = RiskManager()
    result = manager.check(
        1000,
        entry=1.1,
        stop_loss=1.09,
        quality=95,
        risk_per_lot=100,
        total_risk_percent=2.5,
    )

    assert result.allowed is False
    assert result.message == "Maximum total portfolio risk reached"


def test_money_management_approves_volume_within_risk_limit():
    manager = MoneyManagement(RiskManager())
    plan = manager.plan_order(
        balance=1000,
        equity=1000,
        entry=100,
        stop_loss=99,
        requested_volume=0.1,
        quality=90,
        open_positions=0,
        total_risk_percent=0,
        risk_per_lot=100,
        min_lot=0.01,
        max_lot=10,
        lot_step=0.01,
    )
    assert plan.approved is True
    assert plan.approved_volume == 0.1
    assert plan.risk.risk_amount == 10.0


def test_money_management_rejects_volume_above_risk_approved_size():
    manager = MoneyManagement(RiskManager())
    plan = manager.plan_order(
        balance=1000,
        equity=1000,
        entry=100,
        stop_loss=99,
        requested_volume=0.2,
        quality=90,
        open_positions=0,
        total_risk_percent=0,
        risk_per_lot=100,
        min_lot=0.01,
        max_lot=10,
        lot_step=0.01,
    )
    assert plan.approved is False
    assert plan.approved_volume == 0.1


def test_money_management_rejects_daily_equity_drawdown():
    manager = MoneyManagement(RiskManager())
    manager.risk.start_day_balance = 1000
    plan = manager.plan_order(
        balance=1000,
        equity=940,
        entry=100,
        stop_loss=99,
        requested_volume=0.1,
        quality=90,
        open_positions=0,
        total_risk_percent=0,
        risk_per_lot=100,
        min_lot=0.01,
        max_lot=10,
        lot_step=0.01,
    )
    assert plan.approved is False
    assert "drawdown" in plan.message.lower()

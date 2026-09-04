from datetime import date

import pytest

from backtest.forward_test import CompletionTrigger, ForwardTestCycle, ReviewDecision, build_review


def test_cycle_completes_when_100_trades_arrive_before_30_days():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 18), 100)
    assert cycle.completed
    assert cycle.completion_trigger == CompletionTrigger.TRADES
    assert cycle.elapsed_days == 18
    assert cycle.sample_quality == "excellent"


def test_cycle_completes_on_day_30_when_trade_target_is_not_reached():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 30), 63)
    assert cycle.completed
    assert cycle.completion_trigger == CompletionTrigger.DAYS
    assert cycle.sample_quality == "limited"


def test_exactly_100_trades_and_day_30_prioritize_trade_trigger():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 30), 100)
    assert cycle.completion_trigger == CompletionTrigger.TRADES


def test_incomplete_cycle_cannot_be_reviewed():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 10), 20)
    with pytest.raises(ValueError, match="completed cycle"):
        build_review(cycle, ReviewDecision.KEEP, "not enough data")


def test_parameter_changes_are_auditable():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 12), 40)
    updated = cycle.record_parameter_change(
        changed_on=date(2026, 1, 8),
        version_from="v1.0",
        version_to="v1.1",
        reason="reduce weak range entries",
        parameters={"macd_filter": True},
    )
    assert len(updated.parameter_changes) == 1
    assert updated.parameter_changes[0].version_to == "v1.1"
    assert updated.parameter_changes[0].parameters["macd_filter"] is True


def test_trade_count_cannot_move_backwards():
    cycle = ForwardTestCycle(start_date=date(2026, 1, 1)).observe(date(2026, 1, 5), 20)
    with pytest.raises(ValueError, match="cannot decrease"):
        cycle.observe(date(2026, 1, 6), 19)

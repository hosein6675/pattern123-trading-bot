"""Time-and-trade bounded forward-test control for live/demo integrations.

A cycle completes on the first trigger: the trade target or the calendar-day
limit. This module records control state only; it never creates market data,
invents outcomes, or sends broker orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Mapping


class CompletionTrigger(StrEnum):
    TRADES = "trades"
    DAYS = "days"


class ReviewDecision(StrEnum):
    KEEP = "keep"
    MODIFY = "modify"
    REJECT = "reject"
    EXTEND = "extend"


@dataclass(frozen=True, slots=True)
class ParameterChange:
    changed_on: date
    version_from: str
    version_to: str
    reason: str
    parameters: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ForwardTestCycle:
    start_date: date
    trade_target: int = 100
    day_limit: int = 30
    completed_trades: int = 0
    last_observation_date: date | None = None
    parameter_changes: tuple[ParameterChange, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.trade_target <= 0:
            raise ValueError("trade_target must be positive")
        if self.day_limit <= 0:
            raise ValueError("day_limit must be positive")
        if self.completed_trades < 0:
            raise ValueError("completed_trades cannot be negative")
        if self.last_observation_date is not None and self.last_observation_date < self.start_date:
            raise ValueError("last_observation_date cannot precede start_date")

    @property
    def elapsed_days(self) -> int:
        end = self.last_observation_date or self.start_date
        return (end - self.start_date).days + 1

    @property
    def trades_target_reached(self) -> bool:
        return self.completed_trades >= self.trade_target

    @property
    def day_limit_reached(self) -> bool:
        return self.elapsed_days >= self.day_limit

    @property
    def completed(self) -> bool:
        return self.trades_target_reached or self.day_limit_reached

    @property
    def completion_trigger(self) -> CompletionTrigger | None:
        if self.trades_target_reached:
            return CompletionTrigger.TRADES
        if self.day_limit_reached:
            return CompletionTrigger.DAYS
        return None

    @property
    def sample_quality(self) -> str:
        if self.completed_trades >= self.trade_target:
            return "excellent"
        if self.completed_trades >= self.trade_target // 2:
            return "limited"
        return "insufficient"

    def observe(self, observation_date: date, completed_trades: int) -> "ForwardTestCycle":
        if observation_date < self.start_date:
            raise ValueError("observation_date cannot precede start_date")
        if completed_trades < self.completed_trades:
            raise ValueError("completed_trades cannot decrease")
        return ForwardTestCycle(
            start_date=self.start_date,
            trade_target=self.trade_target,
            day_limit=self.day_limit,
            completed_trades=completed_trades,
            last_observation_date=observation_date,
            parameter_changes=self.parameter_changes,
        )

    def record_parameter_change(
        self,
        *,
        changed_on: date,
        version_from: str,
        version_to: str,
        reason: str,
        parameters: Mapping[str, object],
    ) -> "ForwardTestCycle":
        if changed_on < self.start_date:
            raise ValueError("changed_on cannot precede start_date")
        if not reason.strip():
            raise ValueError("reason is required")
        change = ParameterChange(
            changed_on=changed_on,
            version_from=version_from,
            version_to=version_to,
            reason=reason.strip(),
            parameters=dict(parameters),
        )
        return ForwardTestCycle(
            start_date=self.start_date,
            trade_target=self.trade_target,
            day_limit=self.day_limit,
            completed_trades=self.completed_trades,
            last_observation_date=self.last_observation_date,
            parameter_changes=self.parameter_changes + (change,),
        )


@dataclass(frozen=True, slots=True)
class ForwardTestReview:
    cycle: ForwardTestCycle
    decision: ReviewDecision
    rationale: str

    def __post_init__(self) -> None:
        if not self.cycle.completed:
            raise ValueError("review requires a completed cycle")
        if not self.rationale.strip():
            raise ValueError("review rationale is required")


def build_review(cycle: ForwardTestCycle, decision: ReviewDecision, rationale: str) -> ForwardTestReview:
    """Freeze a completed cycle into an auditable review record."""
    return ForwardTestReview(cycle=cycle, decision=decision, rationale=rationale.strip())

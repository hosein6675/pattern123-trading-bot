"""Execution-facing money-management policy.

This module keeps position sizing and portfolio guardrails explicit. It does not
invent market prices, stop distances, or broker constraints; those must come from
validated strategy inputs and the broker adapter.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.risk_manager import RiskManager, RiskResult


@dataclass(frozen=True, slots=True)
class MoneyManagementPlan:
    """Immutable decision produced before an order reaches a broker."""

    approved: bool
    requested_volume: float
    approved_volume: float
    risk: RiskResult
    message: str


class MoneyManagement:
    """Single policy boundary between strategy decisions and broker execution."""

    def __init__(self, risk_manager: RiskManager | None = None):
        self.risk = risk_manager or RiskManager()

    def plan_order(
        self,
        *,
        balance: float,
        equity: float,
        entry: float,
        stop_loss: float,
        requested_volume: float,
        quality: float,
        open_positions: int,
        total_risk_percent: float,
        risk_per_lot: float,
        min_lot: float | None = None,
        max_lot: float | None = None,
        lot_step: float | None = None,
    ) -> MoneyManagementPlan:
        try:
            requested_volume = float(requested_volume)
        except (TypeError, ValueError):
            return MoneyManagementPlan(
                False, 0.0, 0.0,
                self.risk.check(balance=balance, equity=equity, entry=entry, stop_loss=stop_loss, quality=0),
                "Requested volume is invalid",
            )

        if requested_volume <= 0:
            risk = self.risk.check(
                balance=balance, equity=equity, entry=entry, stop_loss=stop_loss,
                quality=quality, open_positions=open_positions,
                total_risk_percent=total_risk_percent, risk_per_lot=risk_per_lot,
                min_lot=min_lot, max_lot=max_lot, lot_step=lot_step,
            )
            return MoneyManagementPlan(False, requested_volume, 0.0, risk, "Requested volume must be greater than zero")

        risk = self.risk.check(
            balance=balance,
            equity=equity,
            entry=entry,
            stop_loss=stop_loss,
            quality=quality,
            open_positions=open_positions,
            total_risk_percent=total_risk_percent,
            risk_per_lot=risk_per_lot,
            min_lot=min_lot,
            max_lot=max_lot,
            lot_step=lot_step,
        )
        if not risk.allowed:
            return MoneyManagementPlan(False, requested_volume, 0.0, risk, risk.message)
        if requested_volume > risk.lot_size + 1e-12:
            return MoneyManagementPlan(
                False, requested_volume, risk.lot_size, risk,
                "Requested volume exceeds risk-approved position size",
            )
        return MoneyManagementPlan(True, requested_volume, requested_volume, risk, "Money-management checks passed")


__all__ = ["MoneyManagement", "MoneyManagementPlan"]

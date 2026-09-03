from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RiskLimits:
    """Hard portfolio guardrails for live and backtest trade sizing."""

    risk_per_trade_percent: float = 1.0
    daily_drawdown_limit: float = 5.0
    max_account_drawdown: float = 20.0
    max_open_positions: int = 5
    max_total_risk_percent: float = 3.0
    max_consecutive_losses: int = 3


@dataclass(frozen=True)
class PositionPlan:
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    volume: float
    risk_amount: float
    risk_percent: float
    reward_risk_ratio: float


class MoneyManager:
    """Deterministic position sizing and risk admission control.

    The manager never invents broker conditions. Monetary risk per lot must be
    supplied by the broker adapter (or a deterministic test adapter).
    """

    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()

    @staticmethod
    def _validate_limits(limits: RiskLimits) -> None:
        if not 0 < limits.risk_per_trade_percent <= 100:
            raise ValueError("risk_per_trade_percent must be in (0, 100]")
        if limits.daily_drawdown_limit < 0 or limits.max_account_drawdown < 0:
            raise ValueError("drawdown limits must be non-negative")
        if limits.max_open_positions < 1:
            raise ValueError("max_open_positions must be at least 1")
        if limits.max_total_risk_percent <= 0:
            raise ValueError("max_total_risk_percent must be positive")
        if limits.max_consecutive_losses < 0:
            raise ValueError("max_consecutive_losses must be non-negative")

    @staticmethod
    def _floor_to_step(value: float, step: float) -> float:
        if step <= 0:
            raise ValueError("lot_step must be positive")
        return math.floor((value + 1e-12) / step) * step

    def admit(
        self,
        *,
        equity: float,
        peak_equity: float,
        daily_start_equity: float,
        open_positions: int,
        current_risk_percent: float,
        consecutive_losses: int,
    ) -> None:
        self._validate_limits(self.limits)
        if equity <= 0 or peak_equity <= 0 or daily_start_equity <= 0:
            raise ValueError("account equity values must be positive")
        if open_positions < 0:
            raise ValueError("open_positions must be non-negative")
        if current_risk_percent < 0:
            raise ValueError("current_risk_percent must be non-negative")
        if consecutive_losses < 0:
            raise ValueError("consecutive_losses must be non-negative")

        account_dd = max((peak_equity - equity) / peak_equity * 100.0, 0.0)
        daily_dd = max((daily_start_equity - equity) / daily_start_equity * 100.0, 0.0)
        if account_dd >= self.limits.max_account_drawdown:
            raise RuntimeError("account drawdown limit reached")
        if daily_dd >= self.limits.daily_drawdown_limit:
            raise RuntimeError("daily drawdown limit reached")
        if open_positions >= self.limits.max_open_positions:
            raise RuntimeError("maximum open positions reached")
        if consecutive_losses >= self.limits.max_consecutive_losses:
            raise RuntimeError("consecutive-loss limit reached")
        if current_risk_percent + self.limits.risk_per_trade_percent > self.limits.max_total_risk_percent + 1e-12:
            raise RuntimeError("maximum portfolio risk reached")

    def plan(
        self,
        *,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        equity: float,
        peak_equity: float,
        daily_start_equity: float,
        risk_per_lot: float,
        volume_min: float,
        volume_max: float,
        volume_step: float,
        open_positions: int = 0,
        current_risk_percent: float = 0.0,
        consecutive_losses: int = 0,
    ) -> PositionPlan:
        direction = str(direction).lower()
        if direction not in {"buy", "sell"}:
            raise ValueError("direction must be buy or sell")
        entry = float(entry)
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)
        risk_per_lot = float(risk_per_lot)
        volume_min = float(volume_min)
        volume_max = float(volume_max)
        volume_step = float(volume_step)
        if not all(math.isfinite(v) for v in (entry, stop_loss, take_profit, risk_per_lot)):
            raise ValueError("trade prices and risk_per_lot must be finite")
        if entry <= 0 or stop_loss <= 0 or take_profit <= 0:
            raise ValueError("trade prices must be positive")
        if direction == "buy" and not (stop_loss < entry < take_profit):
            raise ValueError("buy requires stop_loss < entry < take_profit")
        if direction == "sell" and not (take_profit < entry < stop_loss):
            raise ValueError("sell requires take_profit < entry < stop_loss")
        if risk_per_lot <= 0:
            raise ValueError("risk_per_lot must be positive")
        if volume_min <= 0 or volume_max < volume_min or volume_step <= 0:
            raise ValueError("invalid broker volume contract")

        self.admit(
            equity=equity,
            peak_equity=peak_equity,
            daily_start_equity=daily_start_equity,
            open_positions=open_positions,
            current_risk_percent=current_risk_percent,
            consecutive_losses=consecutive_losses,
        )

        risk_amount = equity * self.limits.risk_per_trade_percent / 100.0
        raw_volume = risk_amount / risk_per_lot
        volume = min(self._floor_to_step(raw_volume, volume_step), volume_max)
        volume = round(volume, 10)
        if volume < volume_min - 1e-12:
            raise RuntimeError("risk budget is below broker minimum volume")

        price_risk = abs(entry - stop_loss)
        price_reward = abs(take_profit - entry)
        rr = price_reward / price_risk
        applied_risk_percent = (risk_per_lot * volume / equity) * 100.0
        if current_risk_percent + applied_risk_percent > self.limits.max_total_risk_percent + 1e-9:
            raise RuntimeError("rounded position exceeds maximum portfolio risk")

        return PositionPlan(
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volume=volume,
            risk_amount=risk_per_lot * volume,
            risk_percent=applied_risk_percent,
            reward_risk_ratio=rr,
        )


__all__ = ["MoneyManager", "PositionPlan", "RiskLimits"]

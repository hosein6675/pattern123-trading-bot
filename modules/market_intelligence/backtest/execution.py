from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionCosts:
    spread: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0

    @property
    def total(self) -> float:
        return self.spread + self.slippage + self.commission


@dataclass(frozen=True)
class ExecutionModel:
    """Deterministic execution-cost model for historical replay.

    Costs are explicit inputs; the model never invents market conditions.
    """

    default_costs: ExecutionCosts = ExecutionCosts()

    def net_pnl(self, gross_pnl: float, costs: ExecutionCosts | None = None) -> float:
        applied = costs if costs is not None else self.default_costs
        return gross_pnl - applied.total

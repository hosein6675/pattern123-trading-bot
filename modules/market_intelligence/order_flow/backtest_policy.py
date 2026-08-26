"""Policies for evaluating order-flow data without contaminating the core strategy."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestPolicy:
    """Defines an isolated experiment using CME/Level-2/order-flow features."""

    enabled: bool = False
    baseline_strategy_only: bool = True
    compare_with_order_flow: bool = False
    allow_forward_bias: bool = False
    require_timestamp_alignment: bool = True
    require_provider_provenance: bool = True

    def validate(self) -> None:
        if self.compare_with_order_flow and not self.enabled:
            raise ValueError("Order-flow comparison requires the order-flow layer to be enabled")
        if self.baseline_strategy_only and self.compare_with_order_flow:
            # Explicitly allowed: this means the backtest should produce both baselines.
            return

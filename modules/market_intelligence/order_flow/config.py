"""Runtime configuration for optional order-flow intelligence."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderFlowConfig:
    """Controls whether external CME/Level-2 intelligence is available to consumers.

    This layer is intentionally opt-in. It never changes Pattern123 decisions by itself.
    """

    enabled: bool = False
    provider: str | None = None
    use_in_strategy: bool = False
    use_in_backtest: bool = False

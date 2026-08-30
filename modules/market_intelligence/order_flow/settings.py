"""Independent runtime controls for optional Level-2 intelligence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderFlowSettings:
    """Level-2 controls are independent from trading strategy selection."""

    enabled: bool = False
    require_live_provider: bool = True

    def validate(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool")
        if not isinstance(self.require_live_provider, bool):
            raise TypeError("require_live_provider must be bool")

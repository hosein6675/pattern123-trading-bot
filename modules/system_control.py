from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class SystemMode(str, Enum):
    MONITOR = "monitor"
    SIGNAL_ONLY = "signal_only"
    AUTO_TRADING = "auto_trading"


@dataclass
class ModuleState:
    enabled: bool = True
    status: str = "unknown"
    last_error: str = ""
    updated_at: str = ""


@dataclass
class SystemControl:
    mode: SystemMode = SystemMode.MONITOR
    emergency_stop: bool = False
    modules: dict[str, ModuleState] = field(default_factory=dict)

    def set_mode(self, mode: SystemMode) -> None:
        self.mode = SystemMode(mode)

    def activate_emergency_stop(self) -> None:
        self.emergency_stop = True

    def release_emergency_stop(self) -> None:
        self.emergency_stop = False

    def can_open_trade(self) -> bool:
        return self.mode is SystemMode.AUTO_TRADING and not self.emergency_stop

    def heartbeat(self, module: str, status: str = "ok", error: str = "") -> None:
        state = self.modules.setdefault(module, ModuleState())
        state.status = status
        state.last_error = error
        state.updated_at = datetime.now(timezone.utc).isoformat()

    def snapshot(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop,
            "modules": {name: vars(state) for name, state in self.modules.items()},
        }


__all__ = ["SystemMode", "ModuleState", "SystemControl"]

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReportLevel(str, Enum):
    PUBLIC = "public"
    STANDARD = "standard"
    SENSITIVE = "sensitive"


@dataclass(frozen=True)
class Destination:
    destination_id: str
    label: str
    kind: str
    report_level: ReportLevel = ReportLevel.PUBLIC
    enabled: bool = True


class DistributionManager:
    """Controls report destinations; sensitive data is never sent to public targets."""

    def __init__(self):
        self.destinations: dict[str, Destination] = {}
        self.delivery_log: list[dict[str, str]] = []

    def register(self, destination: Destination) -> None:
        self.destinations[destination.destination_id] = destination

    def can_deliver(self, destination_id: str, sensitive: bool) -> bool:
        destination = self.destinations.get(destination_id)
        if not destination or not destination.enabled:
            return False
        if sensitive and destination.report_level is not ReportLevel.SENSITIVE:
            return False
        if sensitive and destination.kind in {"group", "channel"} and destination.report_level is not ReportLevel.SENSITIVE:
            return False
        return True

    def record_delivery(self, destination_id: str, report_type: str, status: str) -> None:
        self.delivery_log.append({"destination_id": destination_id, "report_type": report_type, "status": status})


__all__ = ["ReportLevel", "Destination", "DistributionManager"]

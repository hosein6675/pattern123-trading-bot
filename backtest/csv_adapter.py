"""Dependency-free CSV historical price adapter for deterministic backtests."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PriceRecord:
    timestamp: datetime
    price: float


class CsvPriceAdapter:
    """Load timestamp/price records from a local CSV source."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self, start: datetime, end: datetime):
        with self._path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"timestamp", "price"}
            if not required.issubset(reader.fieldnames or set()):
                raise ValueError("CSV must contain timestamp and price columns")
            for row in reader:
                timestamp = datetime.fromisoformat(row["timestamp"])
                price = float(row["price"])
                if start <= timestamp < end:
                    yield PriceRecord(timestamp, price)

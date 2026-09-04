"""Strict CSV OHLC ingestion for real historical validation datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OHLCRecord:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


def load_ohlc_csv(path: str | Path) -> tuple[OHLCRecord, ...]:
    """Load and validate timestamped OHLC rows without altering source data."""
    source = Path(path)
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "open", "high", "low", "close"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV must contain timestamp, open, high, low, close columns")

        records: list[OHLCRecord] = []
        for number, row in enumerate(reader, start=2):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"])
                values = {name: float(row[name]) for name in ("open", "high", "low", "close")}
                volume = float(row["volume"]) if row.get("volume") not in (None, "") else None
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid OHLC row at CSV line {number}") from exc

            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"timestamp at CSV line {number} must include timezone")
            if not all(isfinite(value) and value > 0 for value in values.values()):
                raise ValueError(f"OHLC values at CSV line {number} must be finite and positive")
            if not (values["low"] <= values["open"] <= values["high"] and values["low"] <= values["close"] <= values["high"]):
                raise ValueError(f"OHLC range is invalid at CSV line {number}")
            if volume is not None and (not isfinite(volume) or volume < 0):
                raise ValueError(f"volume at CSV line {number} must be finite and non-negative")

            records.append(OHLCRecord(timestamp=timestamp, volume=volume, **values))

    for previous, current in zip(records, records[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("CSV timestamps must be strictly increasing and unique")
    return tuple(records)

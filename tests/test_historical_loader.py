from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_snapshot import BacktestSnapshot
from backtest.historical import load_snapshots

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Record:
    timestamp: datetime
    price: float


class Adapter:
    def __init__(self, records):
        self.records = records

    def load(self, start, end):
        return self.records


def to_snapshot(record):
    return BacktestSnapshot(record.timestamp, record.price, {})


def test_loader_filters_contract_to_start_end_window():
    records = [
        Record(BASE + timedelta(minutes=2), 102),
        Record(BASE + timedelta(minutes=1), 101),
    ]
    result = load_snapshots(Adapter(records), BASE, BASE + timedelta(minutes=3), to_snapshot)
    assert [item.price for item in result] == [101, 102]


def test_loader_rejects_adapter_leak_before_start():
    records = [Record(BASE - timedelta(seconds=1), 99)]
    with pytest.raises(ValueError, match="before requested start"):
        load_snapshots(Adapter(records), BASE, BASE + timedelta(minutes=1), to_snapshot)


def test_loader_rejects_adapter_leak_at_end():
    records = [Record(BASE + timedelta(minutes=1), 101)]
    with pytest.raises(ValueError, match="at or after requested end"):
        load_snapshots(Adapter(records), BASE, BASE + timedelta(minutes=1), to_snapshot)


def test_loader_rejects_invalid_window():
    with pytest.raises(ValueError, match="after start"):
        load_snapshots(Adapter([]), BASE, BASE, to_snapshot)

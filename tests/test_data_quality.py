from datetime import datetime, timedelta, timezone

import pytest

from backtest.data_quality import validate_rows


def test_quality_gate_accepts_ordered_unique_rows():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    report = validate_rows([{"timestamp": base + timedelta(minutes=i), "price": 100 + i} for i in range(3)])
    assert report.valid


def test_quality_gate_rejects_duplicates_and_out_of_order_rows():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    report = validate_rows([
        {"timestamp": base + timedelta(minutes=1), "price": 101},
        {"timestamp": base, "price": 100},
        {"timestamp": base, "price": 100},
    ])
    assert not report.valid
    assert report.duplicate_timestamps == 1
    assert not report.ordered


def test_quality_gate_counts_missing_fields():
    report = validate_rows([{"timestamp": datetime.now(timezone.utc)}])
    assert not report.valid
    assert report.missing_required == 1

from datetime import datetime, timezone

import pytest

from backtest.csv_adapter import CsvPriceAdapter


def test_csv_adapter_loads_only_requested_interval(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text(
        "timestamp,price\n"
        "2026-01-01T00:00:00+00:00,100\n"
        "2026-01-01T00:01:00+00:00,101\n"
        "2026-01-01T00:02:00+00:00,102\n",
        encoding="utf-8",
    )
    adapter = CsvPriceAdapter(path)
    start = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc)
    rows = tuple(adapter.load(start, end))
    assert [(row.timestamp.minute, row.price) for row in rows] == [(1, 101.0)]


def test_csv_adapter_requires_schema(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("time,value\n", encoding="utf-8")
    with pytest.raises(ValueError, match="timestamp and price"):
        tuple(CsvPriceAdapter(path).load(
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ))

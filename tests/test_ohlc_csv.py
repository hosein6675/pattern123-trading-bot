from pathlib import Path

import pytest

from backtest.ohlc_csv import load_ohlc_csv


def write_csv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "prices.csv"
    path.write_text(body, encoding="utf-8")
    return path


def test_loads_valid_timezone_aware_ohlc(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close,volume\n2026-01-01T00:00:00+00:00,100,105,99,103,10\n2026-01-01T00:01:00+00:00,103,106,102,105,12\n")
    rows = load_ohlc_csv(path)
    assert len(rows) == 2
    assert rows[0].close == 103
    assert rows[1].volume == 12


def test_rejects_duplicate_header(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close,close\n2026-01-01T00:00:00+00:00,100,105,99,103,104\n")
    with pytest.raises(ValueError, match="duplicate column"):
        load_ohlc_csv(path)


def test_rejects_naive_timestamp(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close\n2026-01-01T00:00:00,100,105,99,103\n")
    with pytest.raises(ValueError, match="timezone"):
        load_ohlc_csv(path)


def test_rejects_non_monotonic_timestamps(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close\n2026-01-01T00:01:00+00:00,100,105,99,103\n2026-01-01T00:00:00+00:00,103,106,102,105\n")
    with pytest.raises(ValueError, match="strictly increasing"):
        load_ohlc_csv(path)


def test_rejects_invalid_ohlc_range(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close\n2026-01-01T00:00:00+00:00,108,105,99,103\n")
    with pytest.raises(ValueError, match="OHLC range"):
        load_ohlc_csv(path)


def test_rejects_negative_price(tmp_path: Path):
    path = write_csv(tmp_path, "timestamp,open,high,low,close\n2026-01-01T00:00:00+00:00,-1,105,99,103\n")
    with pytest.raises(ValueError, match="finite and positive"):
        load_ohlc_csv(path)

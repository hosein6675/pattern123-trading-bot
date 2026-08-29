"""Leakage-resistant walk-forward segmentation for backtests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from .data_snapshot import BacktestSnapshot


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    train: tuple[BacktestSnapshot, ...]
    test: tuple[BacktestSnapshot, ...]


def build_windows(
    snapshots: Sequence[BacktestSnapshot],
    train_size: int,
    test_size: int,
) -> tuple[WalkForwardWindow, ...]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    ordered = tuple(snapshots)
    for left, right in zip(ordered, ordered[1:]):
        if right.timestamp < left.timestamp:
            raise ValueError("snapshots must be ordered by timestamp")

    windows: list[WalkForwardWindow] = []
    start = 0
    while start + train_size + test_size <= len(ordered):
        train = ordered[start : start + train_size]
        test = ordered[start + train_size : start + train_size + test_size]
        if train[-1].timestamp >= test[0].timestamp:
            raise ValueError("train and test windows must be strictly chronological")
        windows.append(WalkForwardWindow(train, test))
        start += test_size
    return tuple(windows)

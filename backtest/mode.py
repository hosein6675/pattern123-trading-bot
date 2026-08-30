"""Explicit backtest context modes; no implicit strategy coupling."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum

from .data_snapshot import BacktestSnapshot


class BacktestMode(StrEnum):
    PATTERN_ONLY = "pattern_only"
    NEWS_ONLY = "news_only"
    ORDER_FLOW_ONLY = "order_flow_only"
    COMBINED = "combined"


def context_for(snapshot: BacktestSnapshot, mode: BacktestMode) -> dict[str, object]:
    if mode is BacktestMode.PATTERN_ONLY:
        return {"pattern": snapshot.pattern_data}
    if mode is BacktestMode.NEWS_ONLY:
        return {"news": snapshot.news_data}
    if mode is BacktestMode.ORDER_FLOW_ONLY:
        return {"order_flow": snapshot.order_flow_data}
    if mode is BacktestMode.COMBINED:
        return {
            "pattern": snapshot.pattern_data,
            "news": snapshot.news_data,
            "order_flow": snapshot.order_flow_data,
        }
    raise ValueError(f"unsupported backtest mode: {mode}")


def isolated_snapshot(snapshot: BacktestSnapshot, mode: BacktestMode) -> BacktestSnapshot:
    """Preserve the existing strategy API while removing unselected observations."""
    if mode is BacktestMode.PATTERN_ONLY:
        return replace(snapshot, news_data=(), order_flow_data=())
    if mode is BacktestMode.NEWS_ONLY:
        return replace(snapshot, pattern_data={}, order_flow_data=())
    if mode is BacktestMode.ORDER_FLOW_ONLY:
        return replace(snapshot, pattern_data={}, news_data=())
    if mode is BacktestMode.COMBINED:
        return snapshot
    raise ValueError(f"unsupported backtest mode: {mode}")

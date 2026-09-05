from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from modules.telegram_controls import TelegramSelection


@dataclass(frozen=True, slots=True)
class MultiTimeframeAnalysis:
    symbol: str
    structure_timeframe: str
    analysis_timeframe: str
    trigger_timeframe: str
    structure: Any
    analysis: Any
    trigger: Any
    status: str
    warnings: tuple[str, ...] = ()


def _status(result: Any) -> str:
    if isinstance(result, dict): return str(result.get("status", "unknown"))
    return str(getattr(result, "status", "unknown"))


def analyze(engine: Any, symbol: str, selection: TelegramSelection, candles_by_timeframe: Mapping[str, list[dict[str, Any]]] | None = None) -> MultiTimeframeAnalysis:
    symbol = str(symbol).upper(); candles_by_timeframe = candles_by_timeframe or {}
    structure = engine.analyze_market(symbol, selection.structure_timeframe, candles_by_timeframe.get(selection.structure_timeframe))
    analysis = engine.analyze_market(symbol, selection.analysis_timeframe, candles_by_timeframe.get(selection.analysis_timeframe))
    trigger = engine.analyze_market(symbol, selection.trigger_timeframe, candles_by_timeframe.get(selection.trigger_timeframe))
    warnings: list[str] = []
    for label, timeframe, result in (("ساختار", selection.structure_timeframe, structure), ("تحلیل", selection.analysis_timeframe, analysis), ("تریگر", selection.trigger_timeframe, trigger)):
        if _status(result) != "analysis_complete": warnings.append(f"{label} {timeframe}: {_status(result)}")
    return MultiTimeframeAnalysis(symbol=symbol, structure_timeframe=selection.structure_timeframe, analysis_timeframe=selection.analysis_timeframe, trigger_timeframe=selection.trigger_timeframe, structure=structure, analysis=analysis, trigger=trigger, status="ready" if not warnings else "partial", warnings=tuple(warnings))

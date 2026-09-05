from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    if isinstance(result, dict):
        return str(result.get("status", "unknown"))
    return str(getattr(result, "status", "unknown"))


def analyze(engine: Any, symbol: str, selection: TelegramSelection) -> MultiTimeframeAnalysis:
    symbol = str(symbol).upper()
    structure = engine.analyze_market(symbol, selection.structure_timeframe)
    analysis = engine.analyze_market(symbol, selection.analysis_timeframe)
    trigger = engine.analyze_market(symbol, selection.trigger_timeframe)

    warnings: list[str] = []
    if _status(structure) != "analysis_complete":
        warnings.append(f"ساختار {selection.structure_timeframe}: {_status(structure)}")
    if _status(analysis) != "analysis_complete":
        warnings.append(f"تحلیل {selection.analysis_timeframe}: {_status(analysis)}")
    if _status(trigger) != "analysis_complete":
        warnings.append(f"تریگر {selection.trigger_timeframe}: {_status(trigger)}")

    status = "ready" if not warnings else "partial"
    return MultiTimeframeAnalysis(
        symbol=symbol,
        structure_timeframe=selection.structure_timeframe,
        analysis_timeframe=selection.analysis_timeframe,
        trigger_timeframe=selection.trigger_timeframe,
        structure=structure,
        analysis=analysis,
        trigger=trigger,
        status=status,
        warnings=tuple(warnings),
    )

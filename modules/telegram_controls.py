from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


STRUCTURE_TIMEFRAMES = ("D1", "H4", "H1")
ANALYSIS_TIMEFRAMES = ("H1", "M15", "M5", "M1")
TRIGGER_TIMEFRAMES = ("M15", "M5", "M1")


@dataclass
class TelegramSelection:
    """Per-user Telegram analysis selection; no market data is fabricated here."""

    structure_timeframe: str = "H4"
    analysis_timeframe: str = "M15"
    trigger_timeframe: str = "M1"
    symbols: set[str] = field(default_factory=set)

    def set_structure_timeframe(self, timeframe: str) -> None:
        value = str(timeframe).upper()
        if value not in STRUCTURE_TIMEFRAMES:
            raise ValueError("unsupported structure timeframe")
        self.structure_timeframe = value

    def set_analysis_timeframe(self, timeframe: str) -> None:
        value = str(timeframe).upper()
        if value not in ANALYSIS_TIMEFRAMES:
            raise ValueError("unsupported analysis timeframe")
        self.analysis_timeframe = value

    def set_trigger_timeframe(self, timeframe: str) -> None:
        value = str(timeframe).upper()
        if value not in TRIGGER_TIMEFRAMES:
            raise ValueError("unsupported trigger timeframe")
        self.trigger_timeframe = value

    def toggle_symbol(self, symbol: str, allowed_symbols: set[str]) -> bool:
        value = str(symbol).upper()
        if value not in {item.upper() for item in allowed_symbols}:
            raise ValueError("symbol is not allowed")
        if value in self.symbols:
            self.symbols.remove(value)
            return False
        self.symbols.add(value)
        return True

    def set_symbols(self, symbols: list[str] | tuple[str, ...], allowed_symbols: set[str]) -> None:
        normalized = {str(item).upper() for item in symbols if str(item).strip()}
        if not normalized:
            raise ValueError("at least one symbol is required")
        allowed = {item.upper() for item in allowed_symbols}
        invalid = normalized - allowed
        if invalid:
            raise ValueError("symbol is not allowed")
        self.symbols = normalized


@dataclass(frozen=True)
class AnalysisView:
    symbol: str
    structure_timeframe: str
    analysis_timeframe: str
    trigger_timeframe: str
    decision: str = "NO_TRADE"
    confidence: int | None = None
    structure: str = "unknown"
    trendline: str = "unknown"
    zone: str = "unknown"
    zone_authenticity: str = "unknown"
    price_position: str = "unknown"
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    data_status: str = "unavailable"


def _read(obj: object, name: str, default: object = "unknown") -> object:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def analysis_view_from_result(
    result: object,
    *,
    symbol: str,
    selection: TelegramSelection,
) -> AnalysisView:
    """Adapt a TradingEngine result into a Telegram-safe human-readable view."""
    status = str(_read(result, "status", "unavailable"))
    structure_obj = _read(result, "structure", None)
    context_obj = _read(result, "market_context", None)
    trendline_obj = _read(result, "trendline_fan", None)
    strategy_obj = _read(result, "strategy", None)
    decision_obj = _read(result, "decision", None)
    price_action_obj = _read(result, "price_action", None)

    decision = _read(decision_obj, "decision", _read(result, "decision", "NO_TRADE"))
    confidence = _read(decision_obj, "confidence", None)
    structure = _read(structure_obj, "trend", _read(context_obj, "structure", "unknown"))
    trendline = _read(trendline_obj, "direction", _read(trendline_obj, "trend", "unknown"))
    zone = _read(context_obj, "fib_zone", _read(price_action_obj, "zone", "unknown"))
    authenticity = _read(context_obj, "zone_authenticity", _read(price_action_obj, "zone_authenticity", "unknown"))
    price_position = _read(context_obj, "price_position", _read(price_action_obj, "price_position", "unknown"))
    reasons = _read(strategy_obj, "reasons", _read(decision_obj, "reasons", ()))
    warnings = _read(strategy_obj, "warnings", _read(decision_obj, "warnings", ()))

    return AnalysisView(
        symbol=str(symbol).upper(),
        structure_timeframe=selection.structure_timeframe,
        analysis_timeframe=selection.analysis_timeframe,
        trigger_timeframe=selection.trigger_timeframe,
        decision=str(decision),
        confidence=int(confidence) if confidence is not None else None,
        structure=str(structure),
        trendline=str(trendline),
        zone=str(zone),
        zone_authenticity=str(authenticity),
        price_position=str(price_position),
        reasons=tuple(str(item) for item in reasons) if reasons else (),
        warnings=tuple(str(item) for item in warnings) if warnings else (),
        data_status=status,
    )


def render_analysis(view: AnalysisView) -> str:
    confidence = f"{view.confidence}%" if view.confidence is not None else "نامشخص"
    reasons = "\n".join(f"• {item}" for item in view.reasons) or "• دلیل قابل اتکا در داده فعلی ثبت نشده"
    warnings = "\n".join(f"• {item}" for item in view.warnings) or "• هشدار خاصی ثبت نشده"
    return (
        "📈 گزارش تحلیل Pattern 123\n\n"
        f"🪙 نماد: {view.symbol}\n"
        f"🏗 تایم ساختار: {view.structure_timeframe}\n"
        f"🔎 تایم تحلیل: {view.analysis_timeframe}\n"
        f"🎯 تایم تریگر: {view.trigger_timeframe}\n\n"
        f"🏗 وضعیت ساختار: {view.structure}\n"
        f"📐 وضعیت خط روند: {view.trendline}\n"
        f"📍 منطقه قیمت: {view.zone}\n"
        f"🧪 اصالت منطقه: {view.zone_authenticity}\n"
        f"📌 موقعیت قیمت در منطقه: {view.price_position}\n"
        f"🧠 تصمیم: {view.decision}\n"
        f"🎯 اطمینان: {confidence}\n"
        f"📡 وضعیت دیتا: {view.data_status}\n\n"
        f"✅ دلایل:\n{reasons}\n\n"
        f"⚠️ هشدارها:\n{warnings}"
    )

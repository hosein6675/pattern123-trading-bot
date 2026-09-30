from __future__ import annotations

import io
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont


def _read(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_analysis_chart(result: Mapping[str, Any]) -> bytes:
    """Render the exact MT5 candles attached to an analysis result."""
    candles = list(result.get("chart_candles") or [])
    if len(candles) < 20:
        raise ValueError("analysis chart requires at least 20 MT5 candles")

    width, height = 1500, 900
    left, right, top, bottom = 80, 80, 95, 90
    plot_w, plot_h = width - left - right, height - top - bottom
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    highs = [_num(c.get("high")) for c in candles]
    lows = [_num(c.get("low")) for c in candles]
    hi, lo = max(highs), min(lows)
    pad = max((hi - lo) * 0.08, abs(hi) * 1e-6, 1e-9)
    hi += pad
    lo -= pad

    def xy(index: float, price: float):
        x = left + index / max(len(candles) - 1, 1) * plot_w
        y = top + (hi - price) / (hi - lo) * plot_h
        return x, y

    for i in range(6):
        price = hi - (hi - lo) * i / 5
        _, y = xy(0, price)
        draw.line((left, y, width - right, y), fill="#e5e7eb", width=1)
        draw.text((8, y - 8), f"{price:.5f}", fill="#4b5563", font=_font(15))

    candle_w = max(3, int(plot_w / len(candles) * 0.62))
    for i, c in enumerate(candles):
        o, h, l, close = (_num(c.get(k)) for k in ("open", "high", "low", "close"))
        x, _ = xy(i, close)
        _, yh = xy(i, h)
        _, yl = xy(i, l)
        _, yo = xy(i, o)
        color = "#15803d" if close >= o else "#b91c1c"
        draw.line((x, yh, x, yl), fill=color, width=2)
        y1, y2 = sorted((yo, xy(i, close)[1]))
        draw.rectangle((x - candle_w, y1, x + candle_w, y2), fill=color)

    structure = result.get("structure")
    highs_s = list(_read(structure, "swing_highs", []) or [])
    lows_s = list(_read(structure, "swing_lows", []) or [])

    def mark(point, label, dy=-24):
        idx = int(point.get("index", 0))
        price = _num(point.get("price"))
        if 0 <= idx < len(candles) and price:
            x, y = xy(idx, price)
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), outline="#1d4ed8", width=3)
            draw.text((x + 8, y + dy), label, fill="#1d4ed8", font=_font(18))

    trend = str(_read(structure, "trend", "unknown"))
    if trend == "bullish" and len(lows_s) >= 2 and len(highs_s) >= 1:
        mark(lows_s[-2], "1")
        mark(highs_s[-1], "2")
        mark(lows_s[-1], "3", 18)
    elif trend == "bearish" and len(highs_s) >= 2 and len(lows_s) >= 1:
        mark(highs_s[-2], "1")
        mark(lows_s[-1], "2")
        mark(highs_s[-1], "3", 18)

    fan = result.get("trendline_fan")
    if fan:
        points = lows_s if trend == "bullish" else highs_s
        slope = _num(_read(fan, "support_slope" if trend == "bullish" else "resistance_slope"))
        if len(points) >= 2:
            anchor = points[-2]
            aidx = int(anchor.get("index", 0))
            aprice = _num(anchor.get("price"))
            end_index = len(candles) - 1
            end_price = aprice + slope * (end_index - aidx)
            x1, y1 = xy(aidx, aprice)
            x2, y2 = xy(end_index, end_price)
            draw.line((x1, y1, x2, y2), fill="#7c3aed", width=4)
            draw.text((x1 + 8, y1 - 30), "Trendline", fill="#7c3aed", font=_font(18))

    pa = result.get("price_action")
    for label, field, color in (
        ("Entry", "entry", "#0369a1"),
        ("SL", "stop_loss", "#b91c1c"),
        ("TP1", "tp1", "#15803d"),
        ("TP2", "tp2", "#15803d"),
        ("TP3", "tp3", "#15803d"),
    ):
        price = _num(_read(pa, field, 0))
        if price <= 0:
            continue
        _, y = xy(0, price)
        draw.line((left, y, width - right, y), fill=color, width=2)
        draw.text((width - right + 5, y - 10), f"{label} {price:.5f}", fill=color, font=_font(15))

    symbol = str(result.get("symbol", "")).upper()
    tf = str(result.get("timeframe", ""))
    stf = str(result.get("structure_timeframe", ""))
    ttf = str(result.get("trigger_timeframe", ""))
    decision = str(_read(result.get("decision"), "decision", result.get("decision", "NO_TRADE")))
    trigger = str(_read(result.get("trigger"), "status", ""))
    draw.text((left, 20), f"Pattern 123 | {symbol} | Analysis {tf} | Structure {stf} | Trigger {ttf}",
              fill="#111827", font=_font(26))
    draw.text((left, 53), f"Decision: {decision}    Trigger: {trigger}",
              fill="#111827", font=_font(18))
    draw.text((left, height - 35), "Source: MT5 live observation | No synthetic market data",
              fill="#4b5563", font=_font(15))

    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()

from dataclasses import asdict, is_dataclass
import html
import json


def _plain(value):
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def snapshot(engine, symbol, timeframe, candles=None):
    analysis = engine.analyze_market(symbol, timeframe, candles)
    account = _plain(analysis.get("account")) if isinstance(analysis, dict) else {}
    risk = _plain(analysis.get("risk")) if isinstance(analysis, dict) else {}
    decision = _plain(analysis.get("decision")) if isinstance(analysis, dict) else {}
    strategy = _plain(analysis.get("strategy")) if isinstance(analysis, dict) else {}
    macd = _plain(analysis.get("macd")) if isinstance(analysis, dict) else {}
    context = _plain(analysis.get("market_context")) if isinstance(analysis, dict) else {}
    return {
        "status": analysis.get("status", "unknown") if isinstance(analysis, dict) else "unknown",
        "symbol": str(symbol).upper(),
        "timeframe": str(timeframe).upper(),
        "mode": getattr(engine.orders.broker, "mode", "unknown") if hasattr(engine.orders, "broker") else "unknown",
        "account": account,
        "risk": risk,
        "decision": decision,
        "strategy": strategy,
        "macd": macd,
        "market_context": context,
        "open_positions": analysis.get("open_positions", len(engine.get_open_positions())) if isinstance(analysis, dict) else len(engine.get_open_positions()),
    }


def render(snapshot_data):
    data = _plain(snapshot_data)
    decision = data.get("decision") or {}
    strategy = data.get("strategy") or {}
    risk = data.get("risk") or {}
    macd = data.get("macd") or {}
    context = data.get("market_context") or {}
    account = data.get("account") or {}
    cards = [
        ("Decision", decision.get("decision", "NO_TRADE")),
        ("Direction", decision.get("direction", "none")),
        ("Strategy score", strategy.get("score", 0)),
        ("Risk", f"{risk.get('risk_percent', 0)}%"),
        ("MACD score", macd.get("score", 0)),
        ("Trend", context.get("trend", "unknown")),
        ("Equity", account.get("equity", 0)),
        ("Open positions", data.get("open_positions", 0)),
    ]
    card_html = "".join(f"<div class='card'><span>{html.escape(str(k))}</span><strong>{html.escape(str(v))}</strong></div>" for k, v in cards)
    payload = html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pattern123 Trading Dashboard</title><style>body{{font-family:system-ui,sans-serif;margin:0;background:#101318;color:#f2f4f7}}main{{max-width:1100px;margin:auto;padding:28px}}h1{{margin-bottom:4px}}p{{color:#aeb6c2}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}}.card{{background:#191e26;border:1px solid #2a313c;border-radius:12px;padding:16px}}.card span{{display:block;color:#8f99a8;font-size:12px;text-transform:uppercase}}.card strong{{display:block;font-size:24px;margin-top:8px}}pre{{background:#0b0e12;border:1px solid #242a33;border-radius:12px;padding:16px;overflow:auto;max-height:520px}}</style></head><body><main><h1>Pattern123 Trading Dashboard</h1><p>{html.escape(data.get('symbol',''))} · {html.escape(data.get('timeframe',''))} · status: {html.escape(data.get('status','unknown'))}</p><section class='grid'>{card_html}</section><h2>Analysis payload</h2><pre>{payload}</pre></main></body></html>"""

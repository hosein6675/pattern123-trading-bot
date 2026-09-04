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
    data = _plain(analysis) if isinstance(analysis, dict) else {}
    broker = getattr(getattr(engine, "orders", None), "broker", None)
    data.update({
        "status": data.get("status", "unknown"),
        "symbol": str(symbol).upper(),
        "timeframe": str(timeframe).upper(),
        "mode": str(getattr(broker, "mode", "unknown")),
        "broker_connected": bool(getattr(broker, "connected", False)),
        "open_positions": data.get("open_positions", len(engine.get_open_positions())),
    })
    return data


def _value(data, *keys, default="—"):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def render(snapshot_data):
    data = _plain(snapshot_data)
    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    strategy = data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    risk = data.get("risk") if isinstance(data.get("risk"), dict) else {}
    macd = data.get("macd") if isinstance(data.get("macd"), dict) else {}
    fan = data.get("trendline_fan") if isinstance(data.get("trendline_fan"), dict) else {}
    context = data.get("market_context") if isinstance(data.get("market_context"), dict) else {}
    structure = data.get("structure") if isinstance(data.get("structure"), dict) else {}
    account = data.get("account") if isinstance(data.get("account"), dict) else {}

    cards = [
        ("Decision", decision.get("decision", "NO_TRADE")),
        ("Direction", decision.get("direction", strategy.get("direction", "none"))),
        ("Strategy score", strategy.get("score", 0)),
        ("Confidence", strategy.get("confidence", decision.get("confidence", 0))),
        ("Equity", account.get("equity", 0)),
        ("Risk", f"{risk.get('risk_percent', 0)}%"),
        ("Open positions", data.get("open_positions", 0)),
        ("Mode", data.get("mode", "unknown")),
    ]
    card_html = "".join(
        f"<div class='card'><span>{html.escape(str(k))}</span><strong>{html.escape(str(v))}</strong></div>"
        for k, v in cards
    )

    reasons = strategy.get("reasons", []) or decision.get("reasons", [])
    warnings = strategy.get("warnings", []) or decision.get("warnings", [])
    reasons_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in reasons) or "<li>No positive confirmations</li>"
    warnings_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in warnings) or "<li>No active warnings</li>"

    levels = [
        ("Entry", strategy.get("entry", _value(data, "price_action", "entry", default=0))),
        ("Stop loss", strategy.get("stop_loss", _value(data, "price_action", "stop_loss", default=0))),
        ("TP1", strategy.get("tp1", _value(data, "price_action", "tp1", default=0))),
        ("TP2", strategy.get("tp2", _value(data, "price_action", "tp2", default=0))),
        ("TP3", strategy.get("tp3", _value(data, "price_action", "tp3", default=0))),
        ("R:R", strategy.get("risk_reward", 0)),
    ]
    levels_html = "".join(
        f"<div class='metric'><span>{html.escape(label)}</span><b>{html.escape(str(value))}</b></div>"
        for label, value in levels
    )

    diagnostics = [
        ("Market trend", context.get("trend", "unknown")),
        ("Structure trend", structure.get("trend", "unknown")),
        ("Structure quality", structure.get("structure_quality", 0)),
        ("MACD score", macd.get("score", 0)),
        ("MACD histogram", macd.get("histogram", 0)),
        ("Trendline fan", fan.get("direction", "none")),
        ("Fan score", fan.get("score", 0)),
        ("Daily drawdown", f"{risk.get('daily_drawdown', 0)}%"),
        ("Account drawdown", f"{risk.get('account_drawdown', 0)}%"),
        ("Total risk", f"{risk.get('total_risk_percent', 0)}%"),
        ("Loss streak", risk.get("consecutive_losses", 0)),
        ("Broker connected", data.get("broker_connected", False)),
    ]
    diagnostics_html = "".join(
        f"<div class='metric'><span>{html.escape(label)}</span><b>{html.escape(str(value))}</b></div>"
        for label, value in diagnostics
    )

    payload = html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    symbol = html.escape(str(data.get("symbol", "")))
    timeframe = html.escape(str(data.get("timeframe", "")))
    status = html.escape(str(data.get("status", "unknown")))
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pattern123 Trading Dashboard</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0d1117;color:#e6edf3}}main{{max-width:1200px;margin:auto;padding:24px}}h1{{margin:0 0 6px}}p{{color:#8b949e}}h2{{margin:26px 0 12px;font-size:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:20px 0}}.card,.panel{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px}}.card span,.metric span{{display:block;color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}.card strong{{display:block;font-size:22px;margin-top:7px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.metric{{background:#0d1117;border:1px solid #21262d;border-radius:9px;padding:12px}}.metric b{{display:block;margin-top:5px;font-size:16px;word-break:break-word}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}li{{margin:7px 0}}pre{{background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:14px;overflow:auto;max-height:460px;font-size:12px}}@media(max-width:760px){{.cols{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Pattern123 Trading Dashboard</h1><p>{symbol} · {timeframe} · status: {status}</p>
<section class='grid'>{card_html}</section>
<h2>Execution levels</h2><section class='panel'><div class='metrics'>{levels_html}</div></section>
<h2>Strategy diagnostics</h2><section class='panel'><div class='metrics'>{diagnostics_html}</div></section>
<h2>Decision audit</h2><section class='cols'><div class='panel'><h3>Confirmations</h3><ul>{reasons_html}</ul></div><div class='panel'><h3>Warnings / blockers</h3><ul>{warnings_html}</ul></div></section>
<h2>Analysis payload</h2><pre>{payload}</pre>
</main></body></html>"""

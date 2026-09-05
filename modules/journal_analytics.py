from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from modules.journal import TradeRecord


@dataclass(frozen=True)
class JournalAnalytics:
    total: int
    closed: int
    wins: int
    losses: int
    win_rate: float
    net_profit: float
    avg_profit: float
    by_direction: dict[str, dict[str, float]]
    by_symbol: dict[str, dict[str, float]]
    by_timeframe: dict[str, dict[str, float]]
    best_hours: list[tuple[int, int]]
    repeated_mistakes: list[tuple[str, int, float]]
    repeated_successes: list[tuple[str, int, float]]


def _closed(trades: Iterable[TradeRecord]) -> list[TradeRecord]:
    return [t for t in trades if str(t.result).upper() not in {"OPEN", "PENDING"}]


def _group_stats(trades: list[TradeRecord], key: str) -> dict[str, dict[str, float]]:
    groups: dict[str, list[TradeRecord]] = {}
    for trade in trades:
        value = str(getattr(trade, key)).upper()
        groups.setdefault(value, []).append(trade)
    return {
        name: {
            "count": len(items),
            "wins": sum(t.profit_loss > 0 for t in items),
            "losses": sum(t.profit_loss < 0 for t in items),
            "net_profit": round(sum(t.profit_loss for t in items), 4),
            "win_rate": round(sum(t.profit_loss > 0 for t in items) / len(items) * 100, 2),
        }
        for name, items in groups.items()
    }


def analyze(trades: Iterable[TradeRecord]) -> JournalAnalytics:
    all_trades = list(trades)
    closed = _closed(all_trades)
    wins = sum(t.profit_loss > 0 for t in closed)
    losses = sum(t.profit_loss < 0 for t in closed)
    mistake_counts = Counter(m for t in closed for m in t.mistakes if m)
    success_counts = Counter(f for t in closed if t.profit_loss > 0 for f in t.positive_factors if f)
    hours = Counter()
    for trade in closed:
        try:
            hours[datetime.fromisoformat(trade.entry_time).hour] += 1
        except (TypeError, ValueError):
            continue
    best_hours = hours.most_common(5)
    denominator = max(1, len(closed))
    return JournalAnalytics(
        total=len(all_trades), closed=len(closed), wins=wins, losses=losses,
        win_rate=round(wins / denominator * 100, 2), net_profit=round(sum(t.profit_loss for t in closed), 4),
        avg_profit=round(sum(t.profit_loss for t in closed) / denominator, 4),
        by_direction=_group_stats(closed, "direction"), by_symbol=_group_stats(closed, "symbol"),
        by_timeframe=_group_stats(closed, "timeframe"), best_hours=best_hours,
        repeated_mistakes=[(k, v, round(v / denominator * 100, 2)) for k, v in mistake_counts.most_common()],
        repeated_successes=[(k, v, round(v / denominator * 100, 2)) for k, v in success_counts.most_common()],
    )


def render(analytics: JournalAnalytics) -> str:
    lines = [
        f"Trades: {analytics.total} | Closed: {analytics.closed}",
        f"Win rate: {analytics.win_rate:.2f}% | Net P/L: {analytics.net_profit:.4f}",
        f"Average P/L: {analytics.avg_profit:.4f}",
        "Direction: " + ", ".join(f"{k}={v['count']} ({v['win_rate']:.1f}% WR)" for k, v in analytics.by_direction.items()),
        "Best hours: " + ", ".join(f"{h}:00 ({n})" for h, n in analytics.best_hours),
    ]
    if analytics.repeated_mistakes:
        lines.append("Repeated mistakes: " + ", ".join(f"{k}={n} ({pct:.1f}%)" for k, n, pct in analytics.repeated_mistakes[:5]))
    if analytics.repeated_successes:
        lines.append("Repeated successful factors: " + ", ".join(f"{k}={n} ({pct:.1f}%)" for k, n, pct in analytics.repeated_successes[:5]))
    return "\n".join(lines)


__all__ = ["JournalAnalytics", "analyze", "render"]

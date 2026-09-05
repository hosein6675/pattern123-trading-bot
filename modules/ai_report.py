from __future__ import annotations

from dataclasses import dataclass

from modules.journal import TradeRecord
from modules.journal_analytics import JournalAnalytics, analyze, render


@dataclass(frozen=True)
class AIReport:
    category: str
    strategy_version: str
    summary: str
    warnings: tuple[str, ...]
    recommendations: tuple[str, ...]


class AIReportEngine:
    """Produces structured, evidence-based reports; it never mutates strategy config."""

    def generate(self, trades: list[TradeRecord], category: str = "strategy_review") -> AIReport:
        analytics = analyze(trades)
        warnings: list[str] = []
        recommendations: list[str] = []
        if analytics.win_rate < 45 and analytics.closed >= 20:
            warnings.append("Win rate is below 45%; review entry quality and market filters.")
        for mistake, count, pct in analytics.repeated_mistakes[:3]:
            if count >= 3:
                recommendations.append(f"Review repeated mistake '{mistake}' ({count} trades, {pct:.1f}%).")
        if analytics.best_hours:
            recommendations.append(f"Prioritize review of the strongest observed hour: {analytics.best_hours[0][0]}:00.")
        return AIReport(
            category=category,
            strategy_version=trades[0].strategy_version if trades else "Pattern123 V1",
            summary=render(analytics),
            warnings=tuple(warnings),
            recommendations=tuple(recommendations),
        )

    def generate_if_due(self, trades: list[TradeRecord], batch_size: int = 100) -> AIReport | None:
        if len(trades) == 0 or len(trades) % batch_size != 0:
            return None
        return self.generate(trades, "batch_review")


__all__ = ["AIReport", "AIReportEngine"]

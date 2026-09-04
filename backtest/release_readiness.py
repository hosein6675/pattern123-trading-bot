"""Final release gate for research and trading-runtime safety.

The gate distinguishes software readiness from strategy profitability. It never
creates market data, validation results, broker credentials, or performance
claims. A release is blocked when required evidence or runtime safety settings
are missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from modules.market_intelligence.backtest.execution import ExecutionCosts

from .validation_lab import ValidationLabResult

_PLACEHOLDER_SECRETS = frozenset({"", "change-me", "replace-me", "replace_me"})


@dataclass(frozen=True, slots=True)
class ReleaseCheck:
    name: str
    passed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ReleaseReadiness:
    passed: bool
    checks: tuple[ReleaseCheck, ...]

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(check.reason for check in self.checks if not check.passed)


def _check(name: str, passed: bool, reason: str) -> ReleaseCheck:
    return ReleaseCheck(name=name, passed=passed, reason=reason)


def _costs_are_valid(costs: ExecutionCosts) -> bool:
    return all(
        isfinite(float(value)) and float(value) >= 0
        for value in (costs.spread, costs.slippage, costs.commission)
    )


def evaluate_release_readiness(
    *,
    validation: ValidationLabResult | None,
    execution_costs: ExecutionCosts,
    trading_mode: str,
    live_trading_enabled: bool,
    webhook_secret: str,
    ci_environment: bool = False,
    require_validation: bool = True,
    require_secure_webhook: bool = True,
    required_modes: Iterable[str] | None = None,
) -> ReleaseReadiness:
    """Evaluate deterministic release prerequisites without touching a broker.

    ``require_validation=False`` is intended only for software-only/demo builds.
    Production strategy release should keep validation required.
    """
    checks: list[ReleaseCheck] = []
    normalized_mode = str(trading_mode).strip().lower()

    checks.append(
        _check(
            "execution-costs",
            _costs_are_valid(execution_costs),
            "Execution costs must be finite and non-negative",
        )
    )
    checks.append(
        _check(
            "live-mode-safety",
            not (ci_environment and (normalized_mode == "live" or live_trading_enabled)),
            "CI must never enable live trading",
        )
    )

    if require_secure_webhook:
        secret = str(webhook_secret or "").strip()
        checks.append(
            _check(
                "webhook-secret",
                secret not in _PLACEHOLDER_SECRETS,
                "A non-placeholder webhook secret is required",
            )
        )

    if require_validation:
        validation_present = validation is not None
        checks.append(
            _check(
                "historical-validation",
                validation_present,
                "A real validation result is required; the gate will not invent market evidence",
            )
        )
        if validation_present:
            allowed = set(required_modes or ())
            modes = validation.modes
            if allowed:
                modes = tuple(mode for mode in modes if mode.mode in allowed)
            checks.append(
                _check(
                    "validation-gates",
                    bool(modes) and all(mode.gate.passed for mode in modes),
                    "All required validation modes must pass their configured OOS gates",
                )
            )

    return ReleaseReadiness(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )

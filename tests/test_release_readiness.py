from dataclasses import replace

from backtest.release_readiness import evaluate_release_readiness
from backtest.validation_lab import (
    PerformanceSummary,
    TradeObservation,
    ValidationGate,
    ValidationLabResult,
    ModeValidation,
)
from backtest.mode import BacktestMode
from modules.market_intelligence.backtest.execution import ExecutionCosts


def _summary() -> PerformanceSummary:
    return PerformanceSummary(
        observations=30,
        trades=30,
        wins=20,
        losses=10,
        win_rate=20 / 30,
        net_pnl=10.0,
        gross_profit=20.0,
        gross_loss=10.0,
        profit_factor=2.0,
        expectancy=1 / 3,
        max_drawdown=2.0,
        max_drawdown_pct=0.02,
        sharpe_like=0.5,
        average_win=1.0,
        average_loss=-1.0,
    )


def _validation(passed: bool = True) -> ValidationLabResult:
    summary = _summary()
    mode = ModeValidation(
        mode=BacktestMode.PATTERN_ONLY.value,
        in_sample=summary,
        out_of_sample=summary,
        windows=3,
        gate=ValidationGate(passed, () if passed else ("failed",)),
    )
    return ValidationLabResult((mode,), ExecutionCosts())


def test_release_gate_blocks_placeholder_webhook_secret():
    result = evaluate_release_readiness(
        validation=_validation(),
        execution_costs=ExecutionCosts(),
        trading_mode="demo",
        live_trading_enabled=False,
        webhook_secret="replace-me",
    )
    assert not result.passed
    assert "A non-placeholder webhook secret is required" in result.failures


def test_release_gate_blocks_live_trading_in_ci():
    result = evaluate_release_readiness(
        validation=_validation(),
        execution_costs=ExecutionCosts(),
        trading_mode="live",
        live_trading_enabled=True,
        webhook_secret="real-secret",
        ci_environment=True,
    )
    assert not result.passed
    assert "CI must never enable live trading" in result.failures


def test_release_gate_blocks_missing_validation_evidence():
    result = evaluate_release_readiness(
        validation=None,
        execution_costs=ExecutionCosts(),
        trading_mode="demo",
        live_trading_enabled=False,
        webhook_secret="real-secret",
    )
    assert not result.passed
    assert any("real validation result" in failure for failure in result.failures)


def test_release_gate_passes_only_when_required_evidence_and_safety_checks_pass():
    result = evaluate_release_readiness(
        validation=_validation(),
        execution_costs=ExecutionCosts(spread=1, slippage=0.5, commission=0.2),
        trading_mode="demo",
        live_trading_enabled=False,
        webhook_secret="real-secret",
    )
    assert result.passed
    assert not result.failures


def test_release_gate_rejects_failed_required_validation_mode():
    result = evaluate_release_readiness(
        validation=_validation(passed=False),
        execution_costs=ExecutionCosts(),
        trading_mode="demo",
        live_trading_enabled=False,
        webhook_secret="real-secret",
    )
    assert not result.passed
    assert "All required validation modes must pass their configured OOS gates" in result.failures


def test_release_gate_can_be_used_for_software_only_build_without_validation():
    result = evaluate_release_readiness(
        validation=None,
        execution_costs=ExecutionCosts(),
        trading_mode="demo",
        live_trading_enabled=False,
        webhook_secret="real-secret",
        require_validation=False,
    )
    assert result.passed

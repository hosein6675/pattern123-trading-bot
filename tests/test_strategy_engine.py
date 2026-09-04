from types import SimpleNamespace

from modules.strategy_config import StrategyConfig
from modules.strategy_engine import StrategyEngine


def _inputs(macd_direction="buy", fan_direction="buy", rr_target=3.0):
    structure = SimpleNamespace(trend="bullish", structure_quality=80)
    price_action = SimpleNamespace(
        direction="buy",
        pattern_valid=True,
        confidence=90,
        engulfing=True,
        entry=100.0,
        stop_loss=95.0,
        tp1=105.0,
        tp2=110.0,
        tp3=100.0 + (5.0 * rr_target),
    )
    macd = SimpleNamespace(
        score=80,
        trend_confirmation=macd_direction == "buy",
        histogram=1.0 if macd_direction == "buy" else -1.0,
        momentum_confirmation=True,
    )
    context = SimpleNamespace(trend="bullish", confidence=85)
    fan = SimpleNamespace(direction=fan_direction, score=20)
    return structure, price_action, macd, context, fan


def test_final_strategy_approves_aligned_setup():
    engine = StrategyEngine()
    result = engine.evaluate(*_inputs(), timeframe="M15")
    assert result.approved is True
    assert result.direction == "buy"
    assert result.score == 100
    assert result.confidence == 100
    assert result.risk_reward == 3.0
    assert result.tp3 == 115.0


def test_macd_direction_conflict_fails_closed():
    engine = StrategyEngine()
    result = engine.evaluate(*_inputs(macd_direction="sell"), timeframe="M15")
    assert result.approved is False
    assert result.direction == "buy"
    assert "MACD direction conflict" in result.message


def test_trendline_fan_conflict_fails_closed():
    engine = StrategyEngine()
    result = engine.evaluate(*_inputs(fan_direction="sell"), timeframe="M15")
    assert result.approved is False
    assert "Trendline fan confirmation missing" in result.message


def test_low_risk_reward_fails_closed():
    engine = StrategyEngine()
    result = engine.evaluate(*_inputs(rr_target=1.5), timeframe="M15")
    assert result.approved is False
    assert result.risk_reward == 1.5
    assert "Insufficient risk/reward" in result.message


def test_disallowed_timeframe_fails_closed():
    engine = StrategyEngine()
    result = engine.evaluate(*_inputs(), timeframe="D1")
    assert result.approved is False
    assert result.message == "Timeframe not allowed"


def test_custom_config_can_disable_optional_filters():
    config = StrategyConfig(
        require_engulfing=False,
        use_macd_filter=False,
        require_macd_momentum=False,
        require_trendline_fan=False,
        minimum_trade_quality=55,
        minimum_trade_confidence=55,
    )
    engine = StrategyEngine(config)
    structure, price_action, macd, context, fan = _inputs()
    price_action = SimpleNamespace(**{**price_action.__dict__, "engulfing": False})
    result = engine.evaluate(structure, price_action, macd, context, fan, timeframe="M15")
    assert result.approved is True
    assert result.direction == "buy"

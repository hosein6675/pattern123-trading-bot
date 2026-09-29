from types import SimpleNamespace

from modules.trigger_engine import TriggerEngine


def _inputs(**overrides):
    values = {
        "approved": True,
        "direction": "buy",
        "entry": 100.0,
        "stop_loss": 95.0,
        "tp1": 105.0,
        "tp2": 110.0,
        "tp3": 115.0,
        "risk_reward": 3.0,
    }
    values.update(overrides)
    strategy = SimpleNamespace(**values)
    price_action = SimpleNamespace(engulfing=True)
    macd = SimpleNamespace(momentum_confirmation=True)
    fan = SimpleNamespace(score=80, direction="buy")
    candles = [
        {"volume": 100, "time": 1},
        {"volume": 150, "time": 2},
    ]
    return [strategy, price_action, macd, fan, candles]


def test_trigger_ready_when_all_required_confirmations_pass():
    engine = TriggerEngine()
    result = engine.evaluate(*_inputs())
    assert result.status == "READY"
    assert result.direction == "buy"
    assert result.take_profit == 115.0
    assert result.confirmations["trendline_confirmation"] is True


def test_trigger_rejects_missing_momentum():
    engine = TriggerEngine()
    args = _inputs()
    args[2].momentum_confirmation = False
    result = engine.evaluate(*args)
    assert result.status == "NO_TRADE"
    assert "Momentum confirmation missing" in result.message


def test_trigger_fails_closed_on_invalid_levels():
    engine = TriggerEngine()
    result = engine.evaluate(*_inputs(stop_loss=101.0))
    assert result.status == "NO_TRADE"
    assert "Invalid entry/SL/TP levels" in result.message


def test_trigger_does_not_invent_volume_confirmation():
    engine = TriggerEngine()
    args = _inputs()
    args[-1] = [{"time": 1}, {"time": 2}]
    result = engine.evaluate(*args)
    assert result.status == "READY"
    assert "volume_confirmation" not in result.reasons
    assert "Volume confirmation missing" in result.warnings


def test_trigger_rejects_non_positive_risk_reward_even_with_valid_levels():
    engine = TriggerEngine()
    result = engine.evaluate(*_inputs(risk_reward=0))
    assert result.status == "NO_TRADE"
    assert result.message == "Risk/reward is unavailable"


def test_trigger_rejects_missing_strategy_approval():
    engine = TriggerEngine()
    result = engine.evaluate(*_inputs(approved=False))
    assert result.status == "NO_TRADE"
    assert result.message == "Strategy gate rejected setup"

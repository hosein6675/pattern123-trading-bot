import pytest

from modules.market_intelligence.order_flow.settings import OrderFlowSettings


def test_level2_is_off_by_default():
    settings = OrderFlowSettings()
    assert settings.enabled is False
    assert settings.require_live_provider is True
    settings.validate()


def test_level2_toggle_is_explicit():
    settings = OrderFlowSettings(enabled=True)
    assert settings.enabled is True
    settings.validate()


@pytest.mark.parametrize("field", ["enabled", "require_live_provider"])
def test_settings_reject_non_boolean_values(field):
    kwargs = {field: "yes"}
    with pytest.raises(TypeError):
        OrderFlowSettings(**kwargs).validate()

import pytest

from modules.market_intelligence.order_flow.provider_registry import Level2ProviderRegistry
from modules.market_intelligence.order_flow.settings import OrderFlowSettings


class Provider:
    def snapshots(self):
        return iter(())


def test_enabled_level2_requires_registered_provider():
    registry = Level2ProviderRegistry()
    with pytest.raises(LookupError, match="not registered"):
        registry.create_adapter("cme", OrderFlowSettings(enabled=True))


def test_registered_provider_can_be_enabled_explicitly():
    registry = Level2ProviderRegistry()
    registry.register("cme", Provider())
    adapter = registry.create_adapter("CME", OrderFlowSettings(enabled=True))
    assert adapter.enabled is True


def test_duplicate_provider_registration_is_rejected():
    registry = Level2ProviderRegistry()
    registry.register("cme", Provider())
    with pytest.raises(ValueError, match="already registered"):
        registry.register("CME", Provider())

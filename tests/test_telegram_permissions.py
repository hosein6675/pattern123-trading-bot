from modules.telegram_permissions import TelegramPermissionManager, TelegramRole


def test_unknown_user_is_viewer_without_privileged_access():
    manager = TelegramPermissionManager(admin_ids={10}, trader_ids={20})
    profile = manager.profile_for(999)

    assert profile.role is TelegramRole.VIEWER
    assert profile.can_view is True
    assert profile.can_analyze is True
    assert profile.can_trade is False
    assert profile.can_manage_system is False
    assert profile.can_view_sensitive is False


def test_trader_cannot_manage_system_or_sensitive_data():
    manager = TelegramPermissionManager(admin_ids={10}, trader_ids={20})
    profile = manager.profile_for(20)

    assert profile.role is TelegramRole.TRADER
    assert profile.can_analyze is True
    assert profile.can_trade is True
    assert profile.can_manage_system is False
    assert profile.can_manage_distribution is False
    assert profile.can_view_sensitive is False


def test_admin_has_all_declared_capabilities():
    manager = TelegramPermissionManager(admin_ids={10}, trader_ids={20})
    profile = manager.profile_for(10)

    assert profile.role is TelegramRole.ADMIN
    assert all(
        (
            profile.can_view,
            profile.can_analyze,
            profile.can_trade,
            profile.can_manage_system,
            profile.can_manage_distribution,
            profile.can_view_sensitive,
        )
    )

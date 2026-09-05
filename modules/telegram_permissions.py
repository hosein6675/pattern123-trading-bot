from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from modules.config import active_config


class TelegramRole(str, Enum):
    VIEWER = "viewer"
    TRADER = "trader"
    ADMIN = "admin"


@dataclass(frozen=True)
class PermissionProfile:
    role: TelegramRole
    can_view: bool
    can_analyze: bool
    can_trade: bool
    can_manage_system: bool
    can_manage_distribution: bool
    can_view_sensitive: bool


class TelegramPermissionManager:
    """Fail-closed authorization boundary for Telegram control actions."""

    def __init__(self, admin_ids: set[int] | None = None, trader_ids: set[int] | None = None):
        self.admin_ids = set(admin_ids if admin_ids is not None else active_config.telegram_admin_ids)
        self.trader_ids = set(trader_ids if trader_ids is not None else active_config.telegram_trader_ids)

    def role_for(self, user_id: int | None) -> TelegramRole:
        try:
            uid = int(user_id or 0)
        except (TypeError, ValueError):
            return TelegramRole.VIEWER
        if uid in self.admin_ids:
            return TelegramRole.ADMIN
        if uid in self.trader_ids:
            return TelegramRole.TRADER
        return TelegramRole.VIEWER

    def profile_for(self, user_id: int | None) -> PermissionProfile:
        role = self.role_for(user_id)
        if role is TelegramRole.ADMIN:
            return PermissionProfile(role, True, True, True, True, True, True)
        if role is TelegramRole.TRADER:
            return PermissionProfile(role, True, True, True, False, False, False)
        return PermissionProfile(role, True, True, False, False, False, False)

    def allowed(self, user_id: int | None, capability: str) -> bool:
        profile = self.profile_for(user_id)
        return bool(getattr(profile, capability, False))


__all__ = ["TelegramRole", "PermissionProfile", "TelegramPermissionManager"]

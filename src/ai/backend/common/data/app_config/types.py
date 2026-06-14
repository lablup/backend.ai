from __future__ import annotations

import enum

__all__ = ("AppConfigScopeType",)


class AppConfigScopeType(enum.StrEnum):
    """Scope types for app-config policies and fragments."""

    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"
    USER = "user"

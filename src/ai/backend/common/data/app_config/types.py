"""Shared app config types — the single source for the app config scope enum (BEP-1052)."""

from __future__ import annotations

import enum

from ai.backend.common.data.permission.types import ScopeType

__all__ = ("AppConfigScopeType",)


class AppConfigScopeType(enum.StrEnum):
    """Scope at which an app config fragment is written (BEP-1052).

    The single definition shared across the data, DTO, GraphQL, and API layers.
    """

    PUBLIC = "public"
    DOMAIN = "domain"
    USER = "user"

    def to_rbac_scope_type(self) -> ScopeType:
        """The RBAC scope a write at this fragment scope acts on.

        ``public`` is a system-wide write (``GLOBAL``); ``domain`` / ``user`` act at that
        domain / user scope. This is why writing a fragment is not admin-only — an
        allow-listed user may write their own ``user``-scope fragment.
        """
        match self:
            case AppConfigScopeType.PUBLIC:
                return ScopeType.GLOBAL
            case AppConfigScopeType.DOMAIN:
                return ScopeType.DOMAIN
            case AppConfigScopeType.USER:
                return ScopeType.USER

    def to_rbac_scope_id(self, scope_id: str) -> str:
        """The RBAC scope id for a write at this fragment scope.

        ``public`` is system-wide (no per-entity scope id); ``domain`` / ``user`` carry
        their own ``scope_id``.
        """
        return "" if self is AppConfigScopeType.PUBLIC else scope_id

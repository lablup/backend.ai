"""Shared app config types — the single source for the app config scope enum (BEP-1052)."""

from __future__ import annotations

import enum

from ai.backend.common.data.permission.types import ScopeType

__all__ = ("AppConfigScopeType", "AppConfigPermission")


class AppConfigPermission(enum.StrEnum):
    """What a config layer's scope owner may do with it (BEP-1052).

    Stored per ``(config_name, scope_type)`` on the allow-list, admin-owned (mirrors
    VFolder's ``permission``). It gates writes only — reads always follow scope visibility
    (public → everyone, domain → members, user → owner):

    * ``ro`` — read-only: only a superadmin may write the layer.
    * ``rw`` — read-write: the scope owner may write it (a user their own ``user`` layer),
      and a superadmin always may.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"


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

    def default_rank(self) -> int:
        """Default merge rank for an allow-list entry at this scope type (BEP-1052).

        The merge applies fragments in rank order (low → high; higher wins), so the
        defaults order the scopes as ``public`` < ``domain`` < ``user`` — a user's own
        fragment overrides the domain default, which overrides the public value. The
        100 gap leaves room for admins to place custom ranks in between.
        """
        match self:
            case AppConfigScopeType.PUBLIC:
                return 100
            case AppConfigScopeType.DOMAIN:
                return 200
            case AppConfigScopeType.USER:
                return 300

    def default_permission(self) -> AppConfigPermission:
        """Default write permission for an allow-list entry at this scope type (BEP-1052).

        ``public`` / ``domain`` layers are admin-managed (``ro`` — only a superadmin writes);
        a ``user`` layer is ``rw`` so the owning user manages their own fragment without admin.
        """
        match self:
            case AppConfigScopeType.PUBLIC:
                return AppConfigPermission.READ_ONLY
            case AppConfigScopeType.DOMAIN:
                return AppConfigPermission.READ_ONLY
            case AppConfigScopeType.USER:
                return AppConfigPermission.READ_WRITE

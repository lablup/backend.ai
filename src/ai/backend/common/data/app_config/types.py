"""Shared app config types — the single source for the app config scope enum (BEP-1052)."""

from __future__ import annotations

import enum

from ai.backend.common.data.permission.types import ScopeType

__all__ = ("AppConfigScopeType", "AppConfigAccessLevel")


class AppConfigAccessLevel(enum.StrEnum):
    """Minimum principal tier allowed to read or write a config layer (BEP-1052).

    Ordered least → most privileged: ``public`` < ``authenticated`` < ``owner`` < ``admin``.
    Stored per ``(config_name, scope_type)`` on the allow-list — once for read, once for
    write — so read-enablement and write-authorization are independent concerns. The
    allow-list row's existence no longer implies write access: it only registers the layer
    and its merge ``rank`` (the read side), while ``write_access`` decides who may write.

    ``owner`` is resolved relative to the fragment's scope: the user itself for ``user``
    scope, the domain admin for ``domain``. ``admin`` (superadmin) always satisfies any tier.
    """

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    OWNER = "owner"
    ADMIN = "admin"


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

    def default_read_access(self) -> AppConfigAccessLevel:
        """Default read access for an allow-list entry at this scope type (BEP-1052).

        ``public`` is world-readable (anonymous included); ``domain`` is readable by any
        authenticated caller; a ``user`` layer is readable only by its owner.
        """
        match self:
            case AppConfigScopeType.PUBLIC:
                return AppConfigAccessLevel.PUBLIC
            case AppConfigScopeType.DOMAIN:
                return AppConfigAccessLevel.AUTHENTICATED
            case AppConfigScopeType.USER:
                return AppConfigAccessLevel.OWNER

    def default_write_access(self) -> AppConfigAccessLevel:
        """Default write access for an allow-list entry at this scope type (BEP-1052).

        ``public`` / ``domain`` layers are admin-owned; a ``user`` layer is writable by its
        owner, so an allow-listed user manages their own user-scope fragment without admin.
        """
        match self:
            case AppConfigScopeType.PUBLIC:
                return AppConfigAccessLevel.ADMIN
            case AppConfigScopeType.DOMAIN:
                return AppConfigAccessLevel.ADMIN
            case AppConfigScopeType.USER:
                return AppConfigAccessLevel.OWNER

"""Shared app config types — the single source for the app config scope enum (BEP-1052)."""

from __future__ import annotations

import enum

from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.exception import UnreachableError

__all__ = ("AppConfigScopeType",)


class AppConfigScopeType(enum.StrEnum):
    """Scope at which an app config fragment is written (BEP-1052).

    The single definition shared across the data, DTO, GraphQL, and API layers.
    """

    PUBLIC = "public"
    DOMAIN = "domain"
    USER = "user"

    @classmethod
    def of_owner(cls, owner: EntityIdentifier | None) -> AppConfigScopeType:
        """The scope a fragment owned by ``owner`` is written at; ``None`` is ``public``.

        The inverse of what a fragment's owner id carries: the owner answers its own
        entity type, so the scope does not have to be stored beside it.
        """
        match owner:
            case None:
                return cls.PUBLIC
            case _ if owner.entity_type() == DomainEntityType():
                return cls.DOMAIN
            case _ if owner.entity_type() == UserEntityType():
                return cls.USER
            case _:
                raise UnreachableError(f"No app config scope owns a {owner.entity_type()}")

    def to_owner(self, scope_id: AppConfigScopeID | None) -> EntityIdentifier | None:
        """The entity ``scope_id`` names at this scope; ``public`` names none.

        ``scope_id`` is one value across scope kinds, so its type is settled here, against
        the scope that discriminates it.
        """
        if scope_id is None:
            return None
        match self:
            case AppConfigScopeType.PUBLIC:
                return None
            case AppConfigScopeType.DOMAIN:
                return DomainID(scope_id)
            case AppConfigScopeType.USER:
                return UserID(scope_id)

    def to_rbac_scope_id(self, scope_id: AppConfigScopeID | None) -> str:
        """The RBAC scope id for a write at this fragment scope, in RBAC's string form.

        ``public`` is system-wide and names no owner.
        """
        return "" if self is AppConfigScopeType.PUBLIC else str(scope_id)

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

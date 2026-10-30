from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission


@dataclass(frozen=True)
class OwnCheckKey:
    """A ``(user, entity)`` pair for the own check: which bits the user holds on the
    entity through the scopes that govern a virtual entity owning it."""

    user_id: UserID
    entity: EntityIdentifier


@dataclass(frozen=True)
class GovernCheckKey:
    """A ``(user, scope, entity_type)`` triple for the govern check: which bits the
    user holds on ``entity_type`` within the scope, through the scopes governing the
    scope's virtual entity (itself included)."""

    user_id: UserID
    scope: EntityIdentifier
    entity_type: EntityType


@dataclass(frozen=True)
class PermissionCheckResult:
    """The bits answered for one run's checks: govern per scope key, own per entity key."""

    governed: Mapping[GovernCheckKey, Permission]
    owned: Mapping[OwnCheckKey, Permission]

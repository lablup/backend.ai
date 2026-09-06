from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import UserID


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
    scope: ScopeRef
    entity_type: EntityType

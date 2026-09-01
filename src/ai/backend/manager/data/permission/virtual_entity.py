from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import UserID


@dataclass(frozen=True)
class EntityPermissionCheckKey:
    """Identifies a ``(user, entity)`` target for virtual-entity-chain
    permission resolution.
    """

    user_id: UserID
    entity: EntityIdentifier


@dataclass(frozen=True)
class ScopePermissionCheckKey:
    """Identifies a ``(user, scope)`` target for virtual-entity-chain
    permission resolution.

    The scope itself is walked as an entity (reachable through its own and its
    ancestors' virtual entities), while permission rows are matched on
    ``entity_type`` — the type of entity acted on within the scope.
    """

    user_id: UserID
    scope: ScopeRef
    entity_type: EntityType

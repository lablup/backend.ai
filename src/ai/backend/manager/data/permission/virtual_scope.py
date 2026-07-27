from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef
from ai.backend.common.identifier.user import UserID


@dataclass(frozen=True)
class EntityPermissionCheckKey:
    """Identifies a ``(user, entity)`` target for virtual-scope-chain
    permission resolution.
    """

    user_id: UserID
    entity: EntityRef


@dataclass(frozen=True)
class ScopePermissionCheckKey:
    """Identifies a ``(user, scope)`` target for virtual-scope-chain
    permission resolution.

    The scope itself is walked as an entity (reachable through its own and its
    ancestors' virtual scopes), while permission rows are matched on
    ``subject_entity_type`` — the type of entity acted on within the scope.
    """

    user_id: UserID
    scope: ScopeRef
    subject_entity_type: EntityType

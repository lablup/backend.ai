from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityRef, EntityType
from ai.backend.common.identifier.user import UserID


@dataclass(frozen=True)
class VirtualScopePermissionCheckKey:
    """Identifies a ``(user, entity)`` target for virtual-scope-chain
    permission resolution.

    ``subject_entity_type`` selects which permission rows are consulted at the
    resolved scopes; ``None`` means the entity's own type. Scope-action checks
    set it to the acted-on entity type while ``entity`` is the scope itself.
    """

    user_id: UserID
    entity: EntityRef
    subject_entity_type: EntityType | None = None

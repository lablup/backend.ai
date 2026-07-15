from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.entity.types import EntityRef
from ai.backend.common.identifier.user import UserID


@dataclass(frozen=True)
class VirtualScopePermissionCheckKey:
    """Identifies a ``(user, entity)`` target for virtual-scope-chain
    permission resolution.
    """

    user_id: UserID
    entity: EntityRef

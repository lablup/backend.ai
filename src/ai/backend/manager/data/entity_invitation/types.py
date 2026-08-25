from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import override

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import (
    EntityData,
    EntityID,
    EntityType,
    RuntimeEntityID,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission

__all__ = (
    "EntityInvitationData",
    "EntityInvitationStatus",
)


class EntityInvitationStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"

    @classmethod
    @lru_cache(maxsize=1)
    def unsettled_states(cls) -> frozenset[EntityInvitationStatus]:
        """Every state other than ACCEPTED: still waiting, turned down, or withdrawn.

        Acceptance writes a durable entity membership and the invitation is kept
        beside it as history. The retention sweep removes the rest once their period
        passes, so an invitation nobody answered does not sit forever.
        """
        return frozenset((cls.PENDING, cls.REJECTED, cls.CANCELED))


@dataclass(frozen=True)
class EntityInvitationData(EntityData):
    id: EntityInvitationID
    inviter_user_id: UserID
    invitee_email: str
    target_entity_type: EntityType
    target_entity_id: EntityID
    permission_cap: Permission | None
    status: EntityInvitationStatus
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityInvitationID:
        return self.id

    def target(self) -> RuntimeEntityID:
        """The entity the invitation offers, as an id that answers its own type."""
        return RuntimeEntityID(self.target_entity_type, self.target_entity_id)

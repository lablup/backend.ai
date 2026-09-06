from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityData, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission

__all__ = (
    "EntityShareData",
    "EntityShareStatus",
)


class EntityShareStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"
    REVOKED = "revoked"

    @classmethod
    @lru_cache(maxsize=1)
    def unsettled_states(cls) -> frozenset[EntityShareStatus]:
        """Every state other than ACCEPTED: waiting, turned down, withdrawn, taken back.

        An accepted share holds a graph edge and stays. The retention sweep removes the
        rest once their period passes, so a share nobody answered does not sit forever.
        """
        return frozenset((cls.PENDING, cls.REJECTED, cls.CANCELED, cls.REVOKED))


@dataclass(frozen=True)
class EntityShareData(EntityData):
    id: EntityShareID
    sharer_user_id: UserID
    recipient_virtual_entity_id: VirtualEntityID | None
    recipient_email: str | None
    target: RuntimeEntityID
    permission_cap: Permission | None
    expires_at: datetime | None
    status: EntityShareStatus
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityShareID:
        return self.id

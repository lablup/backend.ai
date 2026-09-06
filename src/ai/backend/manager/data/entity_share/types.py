from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityData, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
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
    def live_states(cls) -> frozenset[EntityShareStatus]:
        """Offered and taken: the two a share stands in.

        One row per recipient and entity stands in these, so offering again to
        somewhere that already holds the entity restates what it lends. The rest have
        ended and pile up beside it.
        """
        return frozenset((cls.PENDING, cls.ACCEPTED))

    @classmethod
    @lru_cache(maxsize=1)
    def terminal_statuses(cls) -> frozenset[EntityShareStatus]:
        """Turned down, withdrawn, taken back: the states an offer stops in.

        An accepted share holds a graph edge and stays; a waiting one is settled by its
        moment passing rather than by age. What is left is history, which the retention
        sweep removes once its period passes.
        """
        return frozenset((cls.REJECTED, cls.CANCELED, cls.REVOKED))


@dataclass(frozen=True)
class EntityShareData(EntityData):
    id: EntityShareID
    sharer_user_id: UserID | None
    recipient: RuntimeEntityID | None
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

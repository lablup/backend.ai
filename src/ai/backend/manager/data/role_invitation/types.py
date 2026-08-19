from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache


class RoleInvitationState(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"

    @classmethod
    @lru_cache(maxsize=1)
    def declined_states(cls) -> frozenset[RoleInvitationState]:
        """Terminal states that did not grant a role (rejected / canceled).

        ACCEPTED is excluded: acceptance writes a durable ``user_roles`` row, but
        the invitation record is kept rather than purged as history.
        """
        return frozenset((cls.REJECTED, cls.CANCELED))


@dataclass(frozen=True)
class RoleInvitationData:
    id: uuid.UUID
    inviter_user_id: uuid.UUID | None
    invitee_user_id: uuid.UUID
    role_id: uuid.UUID
    state: RoleInvitationState
    created_at: datetime
    updated_at: datetime | None

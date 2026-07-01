from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime


class RoleInvitationState(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"


@dataclass(frozen=True)
class RoleInvitationData:
    id: uuid.UUID
    inviter_user_id: uuid.UUID | None
    invitee_user_id: uuid.UUID
    role_id: uuid.UUID
    state: RoleInvitationState
    created_at: datetime
    updated_at: datetime | None

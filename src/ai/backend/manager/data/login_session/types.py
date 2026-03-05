from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


class LoginSessionExpiryReason(enum.StrEnum):
    LOGOUT = "logout"
    EVICTED = "evicted"
    EXPIRED = "expired"


@dataclass(frozen=True)
class LoginSessionData:
    id: UUID
    user_uuid: UUID
    session_token: str
    client_ip: str
    created_at: datetime
    expired_at: datetime | None = field(default=None)
    reason: LoginSessionExpiryReason | None = field(default=None)

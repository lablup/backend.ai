from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.models.login_session.enums import LoginAttemptResult, LoginSessionStatus


@dataclass(frozen=True)
class LoginSessionData:
    id: uuid.UUID
    session_token: str
    user_id: uuid.UUID
    access_key: str
    status: LoginSessionStatus
    created_at: datetime
    last_accessed_at: datetime | None
    invalidated_at: datetime | None


@dataclass(frozen=True)
class LoginHistoryData:
    id: uuid.UUID
    user_id: uuid.UUID
    domain_name: str
    result: LoginAttemptResult
    fail_reason: str | None
    created_at: datetime

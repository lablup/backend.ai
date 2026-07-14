from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime


class LoginSessionStatus(enum.StrEnum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"
    REVOKED = "revoked"


class LoginAttemptResult(enum.StrEnum):
    SUCCESS = "success"
    FAILED_INVALID_CREDENTIALS = "failed_invalid_credentials"
    FAILED_USER_INACTIVE = "failed_user_inactive"
    FAILED_BLOCKED = "failed_blocked"
    FAILED_PASSWORD_EXPIRED = "failed_password_expired"
    FAILED_REJECTED_BY_HOOK = "failed_rejected_by_hook"
    FAILED_SESSION_ALREADY_EXISTS = "failed_session_already_exists"
    LOGOUT = "logout"
    REVOKED_BY_ADMIN = "revoked_by_admin"
    REVOKED_BY_USER = "revoked_by_user"
    EVICTED = "evicted"
    EXPIRED = "expired"


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

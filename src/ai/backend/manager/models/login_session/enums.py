from __future__ import annotations

import enum


class LoginSessionStatus(enum.StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    REVOKED = "revoked"


class LoginAttemptResult(enum.StrEnum):
    SUCCESS = "success"
    FAILED_INVALID_CREDENTIALS = "failed_invalid_credentials"
    FAILED_USER_INACTIVE = "failed_user_inactive"
    FAILED_BLOCKED = "failed_blocked"
    FAILED_PASSWORD_EXPIRED = "failed_password_expired"
    FAILED_REJECTED_BY_HOOK = "failed_rejected_by_hook"

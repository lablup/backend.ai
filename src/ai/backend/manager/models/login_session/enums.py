from __future__ import annotations

import enum


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

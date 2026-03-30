"""Common types for Login History DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "LoginAttemptResult",
    "LoginHistoryOrderField",
    "OrderDirection",
)


class LoginAttemptResult(StrEnum):
    """Result of a login attempt."""

    SUCCESS = "success"
    FAILED_INVALID_CREDENTIALS = "failed_invalid_credentials"
    FAILED_USER_INACTIVE = "failed_user_inactive"
    FAILED_BLOCKED = "failed_blocked"
    FAILED_PASSWORD_EXPIRED = "failed_password_expired"
    FAILED_REJECTED_BY_HOOK = "failed_rejected_by_hook"
    FAILED_SESSION_ALREADY_EXISTS = "failed_session_already_exists"


class LoginHistoryOrderField(StrEnum):
    """Fields available for ordering login history."""

    CREATED_AT = "created_at"
    RESULT = "result"
    DOMAIN_NAME = "domain_name"

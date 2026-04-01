"""Common types for Login Session DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "LoginSessionOrderField",
    "LoginSessionStatus",
    "OrderDirection",
)


class LoginSessionStatus(StrEnum):
    """Status of a login session."""

    ACTIVE = "active"
    INVALIDATED = "invalidated"
    REVOKED = "revoked"


class LoginSessionOrderField(StrEnum):
    """Fields available for ordering login sessions."""

    CREATED_AT = "created_at"
    STATUS = "status"
    LAST_ACCESSED_AT = "last_accessed_at"

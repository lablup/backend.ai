"""
Common types for User DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "UserOrderField",
    "UserRole",
    "UserStatus",
)


class UserStatus(StrEnum):
    """User account status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"


class UserRole(StrEnum):
    """User role values."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class UserOrderField(StrEnum):
    """Fields available for ordering users."""

    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    STATUS = "status"
    DOMAIN_NAME = "domain_name"

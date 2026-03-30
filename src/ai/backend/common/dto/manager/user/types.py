"""
Enum types for user admin REST API DTOs.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "UserOrderField",
    "UserRole",
    "UserStatus",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class UserOrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    STATUS = "status"
    DOMAIN_NAME = "domain_name"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"


class UserRole(StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"

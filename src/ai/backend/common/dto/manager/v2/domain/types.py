"""
Common types for Domain DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

__all__ = (
    "DomainOrderField",
    "DomainProjectFilter",
    "DomainUserFilter",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DomainOrderField(StrEnum):
    """Fields available for ordering domains."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    IS_ACTIVE = "is_active"
    PROJECT_NAME = "project_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


class DomainProjectFilter(BaseRequestModel):
    """Nested filter for projects belonging to a domain."""

    name: StringFilter | None = None
    is_active: bool | None = None


class DomainUserFilter(BaseRequestModel):
    """Nested filter for users belonging to a domain."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None

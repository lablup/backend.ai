"""
Common types for User DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "DomainUserScope",
    "OrderDirection",
    "ProjectUserScope",
    "UserDomainFilter",
    "UserFairShareScope",
    "UserOrderField",
    "UserProjectFilter",
    "UserRole",
    "UserRoleFilter",
    "UserStatus",
    "UserStatusFilter",
    "UserUsageScope",
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


class UserOrderField(StrEnum):
    """Fields available for ordering users."""

    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    STATUS = "status"
    DOMAIN_NAME = "domain_name"
    PROJECT_NAME = "project_name"


class UserStatusFilter(BaseRequestModel):
    """Filter for user status enum fields."""

    equals: UserStatus | None = Field(default=None, description="Exact match for user status.")
    in_: list[UserStatus] | None = Field(
        default=None, alias="in", description="Match any of the provided statuses."
    )
    not_equals: UserStatus | None = Field(default=None, description="Exclude exact status match.")
    not_in: list[UserStatus] | None = Field(
        default=None, description="Exclude any of the provided statuses."
    )


class UserRoleFilter(BaseRequestModel):
    """Filter for user role enum fields."""

    equals: UserRole | None = Field(default=None, description="Exact match for user role.")
    in_: list[UserRole] | None = Field(
        default=None, alias="in", description="Match any of the provided roles."
    )
    not_equals: UserRole | None = Field(default=None, description="Exclude exact role match.")
    not_in: list[UserRole] | None = Field(
        default=None, description="Exclude any of the provided roles."
    )


class UserDomainFilter(BaseRequestModel):
    """Nested filter for the domain a user belongs to."""

    name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    is_active: bool | None = Field(default=None, description="Filter by domain active status.")


class UserProjectFilter(BaseRequestModel):
    """Nested filter for projects a user belongs to."""

    name: StringFilter | None = Field(default=None, description="Filter by project name.")
    is_active: bool | None = Field(default=None, description="Filter by project active status.")


class DomainUserScope(BaseRequestModel):
    """Scope for querying users within a specific domain."""

    domain_name: str = Field(description="Domain name to scope the user query.")


class ProjectUserScope(BaseRequestModel):
    """Scope for querying users within a specific project."""

    project_id: UUID = Field(description="Project UUID to scope the user query.")


class UserFairShareScope(BaseRequestModel):
    """Scope parameters for filtering user fair shares."""

    resource_group_name: str = Field(description="Resource group to filter fair shares by.")
    project_id: UUID = Field(
        description="Project ID that the user belongs to (required for user-level fair shares)."
    )


class UserUsageScope(BaseRequestModel):
    """Scope parameters for filtering user usage buckets."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")
    project_id: UUID = Field(
        description="Project ID that the user belongs to (required for user-level usage)."
    )

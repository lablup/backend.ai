"""
Common types for User DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import EnumFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "DomainUserScope",
    "OrderDirection",
    "ProjectUserScope",
    "UserDomainFilter",
    "UserFairShareScope",
    "UserOrderField",
    "UserProjectFilter",
    "UserRole",
    "UserScope",
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

    ENTITY_ID = "entity_id"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    FULL_NAME = "full_name"
    DESCRIPTION = "description"
    STATUS = "status"
    STATUS_INFO = "status_info"
    ROLE = "role"
    DOMAIN_NAME = "domain_name"
    DOMAIN_ID = "domain_id"
    INTEGRATION_NAME = "integration_name"
    RESOURCE_POLICY = "resource_policy"
    NEED_PASSWORD_CHANGE = "need_password_change"
    TOTP_ACTIVATED = "totp_activated"
    TOTP_ACTIVATED_AT = "totp_activated_at"
    SUDO_SESSION_ENABLED = "sudo_session_enabled"
    CONTAINER_UID = "container_uid"
    CONTAINER_MAIN_GID = "container_main_gid"
    PROJECT_NAME = "project_name"


class UserStatusFilter(EnumFilter[UserStatus]):
    """Filter for user status enum fields."""


class UserRoleFilter(EnumFilter[UserRole]):
    """Filter for user role enum fields."""


class UserDomainFilter(BaseRequestModel):
    """Deprecated. Nested filter for the domain a user belongs to."""

    name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    is_active: bool | None = Field(default=None, description="Filter by domain active status.")


class UserProjectFilter(BaseRequestModel):
    """Deprecated. Nested filter for projects a user belongs to."""

    name: StringFilter | None = Field(default=None, description="Filter by project name.")
    is_active: bool | None = Field(default=None, description="Filter by project active status.")


class DomainUserScope(BaseRequestModel):
    """Scope for querying users within a specific domain."""

    domain_name: str = Field(description="Domain name to scope the user query.")


class UserScope(BaseRequestModel):
    """Scope for the scoped user query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose users are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose users are being read"
    )
    role: list[UUIDScope] | None = Field(
        default=None, description="Roles whose holders are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> UserScope:
        if not self.domain and not self.project and not self.role:
            raise ValueError(
                "UserScope requires a non-empty value for 'domain', 'project' or 'role'"
            )
        return self


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

"""
Request DTOs for User v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserOrderField,
    UserRole,
    UserStatus,
)

__all__ = (
    "CreateUserInput",
    "DeleteUserInput",
    "PurgeUserInput",
    "SearchUsersRequest",
    "UpdateUserInput",
    "UserFilter",
    "UserOrder",
)


class CreateUserInput(BaseRequestModel):
    """Input for creating a new user."""

    email: str = Field(description="User's email address. Must be unique across the system.")
    username: str = Field(description="Unique username for login.")
    password: str = Field(description="Initial password for the user.")
    domain_name: str = Field(description="Domain to assign the user to.")
    need_password_change: bool = Field(
        default=False,
        description="If true, user must change password on first login.",
    )
    status: UserStatus = Field(description="Initial account status.")
    role: UserRole = Field(description="User role determining access permissions.")
    full_name: str | None = Field(
        default=None,
        description="User's full display name.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description or notes about the user.",
    )
    group_ids: list[UUID] | None = Field(
        default=None,
        description="List of project (group) IDs to assign the user to.",
    )
    allowed_client_ip: list[str] | None = Field(
        default=None,
        description="Allowed client IP addresses or CIDR ranges.",
    )
    totp_activated: bool = Field(
        default=False,
        description="Whether to enable TOTP two-factor authentication.",
    )
    resource_policy: str = Field(
        default="default",
        description="Name of the user resource policy to apply.",
    )
    sudo_session_enabled: bool = Field(
        default=False,
        description="Whether this user can create sudo sessions.",
    )
    container_uid: int | None = Field(
        default=None,
        description="User ID (UID) for container processes.",
    )
    container_main_gid: int | None = Field(
        default=None,
        description="Primary group ID (GID) for container processes.",
    )
    container_gids: list[int] | None = Field(
        default=None,
        description="Supplementary group IDs for container processes.",
    )


class UpdateUserInput(BaseRequestModel):
    """Input for updating user information. All fields optional — only provided fields will be updated."""

    username: str | None = Field(
        default=None,
        description="New username.",
    )
    password: str | None = Field(
        default=None,
        description="New password.",
    )
    full_name: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New full display name. Set to null to clear.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New description. Set to null to clear.",
    )
    status: UserStatus | None = Field(
        default=None,
        description="New account status.",
    )
    role: UserRole | None = Field(
        default=None,
        description="New user role.",
    )
    domain_name: str | None = Field(
        default=None,
        description="New domain assignment.",
    )
    group_ids: list[UUID] | Sentinel | None = Field(
        default=SENTINEL,
        description="New project (group) assignments. Replaces existing assignments. Set to null to clear.",
    )
    allowed_client_ip: list[str] | Sentinel | None = Field(
        default=SENTINEL,
        description="New allowed client IP addresses or CIDR ranges. Set to null to allow all.",
    )
    need_password_change: bool | None = Field(
        default=None,
        description="Set password change requirement.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="New user resource policy name.",
    )
    sudo_session_enabled: bool | None = Field(
        default=None,
        description="Enable or disable sudo session capability.",
    )
    main_access_key: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Set the primary API access key. Set to null to clear.",
    )
    container_uid: int | Sentinel | None = Field(
        default=SENTINEL,
        description="New container user ID. Set to null to clear.",
    )
    container_main_gid: int | Sentinel | None = Field(
        default=SENTINEL,
        description="New container primary group ID. Set to null to clear.",
    )
    container_gids: list[int] | Sentinel | None = Field(
        default=SENTINEL,
        description="New container supplementary group IDs. Set to null to clear.",
    )


class DeleteUserInput(BaseRequestModel):
    """Input for soft-deleting a user."""

    user_id: UUID = Field(description="UUID of the user to soft-delete.")


class PurgeUserInput(BaseRequestModel):
    """Input for permanently deleting a user and all associated data."""

    user_id: UUID = Field(description="UUID of the user to purge.")
    purge_shared_vfolders: bool = Field(
        default=False,
        description="If true, migrate shared virtual folders to the admin user before purging.",
    )
    delegate_endpoint_ownership: bool = Field(
        default=False,
        description="If true, delegate endpoint ownership to the admin user before purging.",
    )


class UserFilter(BaseRequestModel):
    """Filter criteria for searching users."""

    uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID.")
    email: StringFilter | None = Field(default=None, description="Filter by email.")
    username: StringFilter | None = Field(default=None, description="Filter by username.")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    status: list[UserStatus] | None = Field(default=None, description="Filter by user statuses.")
    role: list[UserRole] | None = Field(default=None, description="Filter by user roles.")


class UserOrder(BaseRequestModel):
    """Order specification for user search results."""

    field: UserOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Order direction.",
    )


class SearchUsersRequest(BaseRequestModel):
    """Request body for searching users with filters, orders, and pagination."""

    filter: UserFilter | None = Field(default=None, description="Filter conditions.")
    order: list[UserOrder] | None = Field(default=None, description="Order specifications.")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return.",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip.")

"""
Request DTOs for User v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserDomainFilter,
    UserOrderField,
    UserProjectFilter,
    UserRole,
    UserRoleFilter,
    UserStatus,
    UserStatusFilter,
)

__all__ = (
    "AdminSearchUsersInput",
    "BulkCreateUsersInput",
    "BulkPurgeUsersInput",
    "BulkPurgeUsersOptions",
    "BulkUpdateUserItemInput",
    "BulkUpdateUsersInput",
    "CreateUserInput",
    "DeleteUserInput",
    "DeleteUsersInput",
    "PurgeUserInput",
    "PurgeUserV2Input",
    "SearchUsersRequest",
    "UpdateMyAllowedClientIPInput",
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


class BulkCreateUsersInput(BaseRequestModel):
    """Input for creating multiple users in bulk."""

    users: list[CreateUserInput] = Field(description="List of user creation inputs.")


class BulkUpdateUserItemInput(BaseRequestModel):
    """Input for a single user update within a bulk operation."""

    user_id: UUID = Field(description="UUID of the user to update.")
    input: UpdateUserInput = Field(description="Fields to update for this user.")


class BulkUpdateUsersInput(BaseRequestModel):
    """Input for bulk updating multiple users."""

    users: list[BulkUpdateUserItemInput] = Field(description="List of user update inputs.")


class DeleteUsersInput(BaseRequestModel):
    """Input for soft-deleting multiple users."""

    user_ids: list[UUID] = Field(description="List of user UUIDs to soft-delete.")


class PurgeUserV2Input(BaseRequestModel):
    """Input for permanently deleting a single user (GQL-aligned, user_id only)."""

    user_id: UUID = Field(description="UUID of the user to purge.")


class BulkPurgeUsersOptions(BaseRequestModel):
    """Options for bulk user purge operation."""

    purge_shared_vfolders: bool = Field(
        default=False,
        description="If true, migrate shared virtual folders to the admin user before purging.",
    )
    delegate_endpoint_ownership: bool = Field(
        default=False,
        description="If true, delegate endpoint ownership to the admin user before purging.",
    )


class BulkPurgeUsersInput(BaseRequestModel):
    """Input for permanently deleting multiple users in bulk."""

    user_ids: list[UUID] = Field(description="List of user UUIDs to purge.")
    options: BulkPurgeUsersOptions | None = Field(
        default=None, description="Options for the purge operation."
    )


class UpdateMyAllowedClientIPInput(BaseRequestModel):
    """Input for updating the current user's allowed client IP list."""

    allowed_client_ip: list[str] | None = Field(
        description=(
            "New allowed client IP addresses or CIDR ranges. "
            "Set to null to remove all IP restrictions."
        )
    )
    force: bool = Field(
        default=False,
        description=(
            "If false (default), the operation will fail if the current request IP "
            "is not included in the new allowlist."
        ),
    )


class UserFilter(BaseRequestModel):
    """Filter criteria for searching users."""

    uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID.")
    username: StringFilter | None = Field(default=None, description="Filter by username.")
    email: StringFilter | None = Field(default=None, description="Filter by email.")
    status: UserStatusFilter | None = Field(default=None, description="Filter by account status.")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    role: UserRoleFilter | None = Field(default=None, description="Filter by user role.")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation timestamp."
    )
    domain: UserDomainFilter | None = Field(
        default=None, description="Nested filter for the domain a user belongs to."
    )
    project: UserProjectFilter | None = Field(
        default=None, description="Nested filter for projects a user belongs to."
    )
    AND: list[UserFilter] | None = Field(
        default=None, description="Combine multiple filters with AND logic."
    )
    OR: list[UserFilter] | None = Field(
        default=None, description="Combine multiple filters with OR logic."
    )
    NOT: list[UserFilter] | None = Field(default=None, description="Negate the specified filters.")


UserFilter.model_rebuild()


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


class AdminSearchUsersInput(BaseRequestModel):
    """Input for searching users with cursor or offset pagination (GQL-aligned)."""

    filter: UserFilter | None = Field(default=None, description="Filter conditions.")
    order: list[UserOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(
        default=None, description="Forward cursor pagination: number of items."
    )
    after: str | None = Field(default=None, description="Forward cursor pagination: cursor.")
    last: int | None = Field(
        default=None, description="Backward cursor pagination: number of items."
    )
    before: str | None = Field(default=None, description="Backward cursor pagination: cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: starting position.")

"""
Response DTOs for User v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.user.types import UserRole, UserStatus

__all__ = (
    "AdminSearchUsersPayload",
    "BulkCreateUserV2Error",
    "BulkCreateUsersPayload",
    "BulkPurgeUserV2Error",
    "BulkPurgeUsersPayload",
    "BulkUpdateUserV2Error",
    "BulkUpdateUsersPayload",
    "CreateUserPayload",
    "DeleteUserPayload",
    "DeleteUsersPayload",
    "EntityTimestamps",
    "PurgeUserPayload",
    "PurgeUsersPayload",
    "SearchUsersPayload",
    "UpdateMyAllowedClientIPPayload",
    "UpdateUserPayload",
    "UserBasicInfo",
    "UserContainerSettings",
    "UserNode",
    "UserOrganizationInfo",
    "UserPayload",
    "UserSecurityInfo",
    "UserStatusInfo",
)


class UserBasicInfo(BaseModel):
    """Basic user profile information."""

    username: str | None = Field(
        default=None,
        description="Unique username for login. May be null if only email-based login is used.",
    )
    email: str = Field(
        description="User's email address. Used for login and notifications.",
    )
    full_name: str | None = Field(
        default=None,
        description="User's full display name.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description or notes about the user.",
    )
    integration_name: str | None = Field(
        default=None,
        description="External system integration identifier.",
    )


class UserStatusInfo(BaseModel):
    """User account status information."""

    status: UserStatus = Field(
        description=(
            "Current account status. See UserStatus enum for possible values. "
            "Replaces the deprecated is_active field."
        ),
    )
    status_info: str | None = Field(
        default=None,
        description="Additional information about the current status, such as reason for deactivation.",
    )
    need_password_change: bool | None = Field(
        default=None,
        description="If true, user must change password on next login.",
    )


class UserOrganizationInfo(BaseModel):
    """User's organizational context and permissions."""

    domain_name: str | None = Field(
        default=None,
        description="Name of the domain this user belongs to.",
    )
    role: UserRole | None = Field(
        default=None,
        description="User's role determining access permissions. See UserRole enum.",
    )
    resource_policy: str = Field(
        description="Name of the user resource policy applied to this user.",
    )
    main_access_key: str | None = Field(
        default=None,
        description="Primary API access key for this user.",
    )


class UserSecurityInfo(BaseModel):
    """User security settings and authentication configuration."""

    allowed_client_ip: list[str] | None = Field(
        default=None,
        description=(
            "List of allowed client IP addresses or CIDR ranges. "
            "If set, login is restricted to these IP addresses. "
            "Supports both IPv4 and IPv6 formats (e.g., '192.168.1.0/24', '::1')."
        ),
    )
    totp_activated: bool | None = Field(
        default=None,
        description="Whether TOTP (Time-based One-Time Password) two-factor authentication is enabled.",
    )
    totp_activated_at: datetime | None = Field(
        default=None,
        description="Timestamp when TOTP was activated.",
    )
    sudo_session_enabled: bool = Field(
        description="Whether this user can create sudo (privileged) sessions.",
    )


class UserContainerSettings(BaseModel):
    """Container execution settings for the user."""

    container_uid: int | None = Field(
        default=None,
        description="User ID (UID) to use inside containers. If null, system default is used.",
    )
    container_main_gid: int | None = Field(
        default=None,
        description="Primary group ID (GID) to use inside containers. If null, system default is used.",
    )
    container_gids: list[int] | None = Field(
        default=None,
        description="Additional supplementary group IDs for container processes.",
    )


class EntityTimestamps(BaseModel):
    """Common timestamp fields for entity lifecycle tracking."""

    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when this entity was created.",
    )
    modified_at: datetime | None = Field(
        default=None,
        description="Timestamp when this entity was last modified.",
    )


class UserNode(BaseResponseModel):
    """User entity with structured field groups."""

    id: UUID = Field(
        description="Unique identifier for the user (UUID).",
    )
    basic_info: UserBasicInfo = Field(
        description="Basic profile information including username, email, and display name.",
    )
    status: UserStatusInfo = Field(
        description="Account status and password-related flags.",
    )
    organization: UserOrganizationInfo = Field(
        description="Organizational context including domain, role, and resource policy.",
    )
    security: UserSecurityInfo = Field(
        description="Security settings including IP restrictions and TOTP configuration.",
    )
    container: UserContainerSettings = Field(
        description="Container execution settings including UID/GID mappings.",
    )
    timestamps: EntityTimestamps = Field(
        description="Creation and modification timestamps.",
    )


class UserPayload(BaseResponseModel):
    """Payload for single user mutation responses."""

    user: UserNode = Field(
        description="The user entity.",
    )


class SearchUsersPayload(BaseResponseModel):
    """Payload for user search responses."""

    items: list[UserNode] = Field(
        description="List of user entities matching the search criteria.",
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for the result set.",
    )


class DeleteUserPayload(BaseResponseModel):
    """Payload for user deletion mutation."""

    success: bool = Field(
        description="Whether the deletion was successful.",
    )


class DeleteUsersPayload(BaseResponseModel):
    """Payload for bulk user soft-delete mutation."""

    deleted_count: int = Field(
        description="Number of users successfully soft-deleted.",
    )


class PurgeUserPayload(BaseResponseModel):
    """Payload for user permanent deletion mutation."""

    success: bool = Field(
        description="Whether the purge was successful.",
    )


class PurgeUsersPayload(BaseResponseModel):
    """Payload for bulk user permanent deletion mutation."""

    purged_count: int = Field(
        description="Number of users successfully purged.",
    )
    failed_user_ids: list[UUID] = Field(
        description="List of user UUIDs that failed to purge, if any.",
    )


class BulkCreateUserV2Error(BaseResponseModel):
    """Error information for a single user that failed during bulk creation."""

    index: int = Field(description="Original position in the input list.")
    username: str = Field(description="Username of the user that failed.")
    email: str = Field(description="Email of the user that failed.")
    message: str = Field(description="Error message describing the failure.")


class BulkUpdateUserV2Error(BaseResponseModel):
    """Error information for a single user that failed during bulk update."""

    user_id: UUID = Field(description="UUID of the user that failed to update.")
    message: str = Field(description="Error message describing the failure.")


class BulkPurgeUserV2Error(BaseResponseModel):
    """Error information for a single user that failed during bulk purge."""

    user_id: UUID = Field(description="UUID of the user that failed to purge.")
    message: str = Field(description="Error message describing the failure.")


class BulkPurgeUsersPayload(BaseResponseModel):
    """Payload for bulk user permanent deletion mutation."""

    purged_count: int = Field(description="Number of users successfully purged.")
    failed: list[BulkPurgeUserV2Error] = Field(
        description="List of errors for users that failed to purge.",
    )


class UpdateMyAllowedClientIPPayload(BaseResponseModel):
    """Payload for updating the current user's allowed client IP list."""

    success: bool = Field(description="Whether the update was successful.")


class CreateUserPayload(BaseResponseModel):
    """Payload for single user creation mutation."""

    user: UserNode = Field(description="The newly created user.")


class UpdateUserPayload(BaseResponseModel):
    """Payload for user update mutation."""

    user: UserNode = Field(description="The updated user.")


class BulkCreateUsersPayload(BaseResponseModel):
    """Payload for bulk user creation mutation."""

    created_users: list[UserNode] = Field(description="List of successfully created users.")
    failed: list[BulkCreateUserV2Error] = Field(
        description="List of errors for users that failed to create."
    )


class BulkUpdateUsersPayload(BaseResponseModel):
    """Payload for bulk user update mutation."""

    updated_users: list[UserNode] = Field(description="List of successfully updated users.")
    failed: list[BulkUpdateUserV2Error] = Field(
        description="List of errors for users that failed to update."
    )


class AdminSearchUsersPayload(BaseResponseModel):
    """Payload for searching users with cursor-based or offset pagination."""

    items: list[UserNode] = Field(description="List of user nodes matching the query.")
    total_count: int = Field(description="Total number of users matching the query criteria.")
    has_next_page: bool = Field(description="Whether there are more items after this page.")
    has_previous_page: bool = Field(description="Whether there are more items before this page.")

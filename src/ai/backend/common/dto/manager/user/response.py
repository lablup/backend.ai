"""
Response DTOs for user admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import UserRole, UserStatus

__all__ = (
    "CreateUserResponse",
    "DeleteUserResponse",
    "GetUserResponse",
    "PaginationInfo",
    "PurgeUserResponse",
    "SearchUsersResponse",
    "UpdateUserResponse",
    "UserDTO",
)


class UserDTO(BaseModel):
    """DTO for user data in REST API responses."""

    id: UUID = Field(description="User UUID")
    username: str | None = Field(default=None, description="Username")
    email: str = Field(description="User email address")
    need_password_change: bool | None = Field(
        default=None, description="Whether user needs to change password"
    )
    full_name: str | None = Field(default=None, description="Full name")
    description: str | None = Field(default=None, description="User description")
    status: UserStatus = Field(description="User account status")
    status_info: str | None = Field(default=None, description="Status information")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    modified_at: datetime | None = Field(default=None, description="Last modification timestamp")
    domain_name: str | None = Field(default=None, description="Domain name")
    role: UserRole | None = Field(default=None, description="User role")
    resource_policy: str = Field(description="Resource policy name")
    allowed_client_ip: list[str] | None = Field(
        default=None, description="Allowed client IP addresses"
    )
    totp_activated: bool | None = Field(default=None, description="Whether TOTP is activated")
    sudo_session_enabled: bool = Field(description="Whether sudo session is enabled")
    main_access_key: str | None = Field(default=None, description="Main access key")
    container_uid: int | None = Field(default=None, description="Container UID")
    container_main_gid: int | None = Field(default=None, description="Container main GID")
    container_gids: list[int] | None = Field(default=None, description="Container additional GIDs")


class PaginationInfo(BaseModel):
    """Pagination information for search results."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items returned")


class CreateUserResponse(BaseResponseModel):
    """Response for creating a user."""

    user: UserDTO = Field(description="Created user")


class GetUserResponse(BaseResponseModel):
    """Response for getting a user."""

    user: UserDTO = Field(description="User data")


class SearchUsersResponse(BaseResponseModel):
    """Response for searching users."""

    items: list[UserDTO] = Field(description="List of users")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateUserResponse(BaseResponseModel):
    """Response for updating a user."""

    user: UserDTO = Field(description="Updated user")


class DeleteUserResponse(BaseResponseModel):
    """Response for deleting a user."""

    success: bool = Field(description="Whether the user was deleted")


class PurgeUserResponse(BaseResponseModel):
    """Response for purging a user."""

    success: bool = Field(description="Whether the user was purged")

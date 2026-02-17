"""
Request DTOs for user admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import OrderDirection, UserOrderField, UserRole, UserStatus

__all__ = (
    "CreateUserRequest",
    "DeleteUserRequest",
    "PurgeUserRequest",
    "SearchUsersRequest",
    "UpdateUserRequest",
    "UserFilter",
    "UserOrder",
)


class CreateUserRequest(BaseRequestModel):
    """Request to create a new user."""

    email: str = Field(description="User email address")
    username: str = Field(description="Username")
    password: str = Field(description="User password")
    need_password_change: bool = Field(
        default=False, description="Whether user needs to change password on first login"
    )
    domain_name: str = Field(description="Domain the user belongs to")
    full_name: str | None = Field(default=None, description="Full name of the user")
    description: str | None = Field(default=None, description="User description")
    status: UserStatus | None = Field(default=None, description="User account status")
    role: UserRole | None = Field(default=None, description="User role")
    allowed_client_ip: list[str] | None = Field(
        default=None, description="Allowed client IP addresses"
    )
    totp_activated: bool | None = Field(default=None, description="Whether TOTP is activated")
    resource_policy: str | None = Field(default=None, description="Resource policy name")
    sudo_session_enabled: bool | None = Field(
        default=None, description="Whether sudo session is enabled"
    )
    container_uid: int | None = Field(default=None, description="Container UID")
    container_main_gid: int | None = Field(default=None, description="Container main GID")
    container_gids: list[int] | None = Field(default=None, description="Container additional GIDs")
    group_ids: list[str] | None = Field(default=None, description="Group IDs to assign the user to")


class UpdateUserRequest(BaseRequestModel):
    """Request to update an existing user."""

    username: str | None = Field(default=None, description="Updated username")
    password: str | None = Field(default=None, description="Updated password")
    need_password_change: bool | None = Field(
        default=None, description="Updated need_password_change flag"
    )
    full_name: str | None = Field(default=None, description="Updated full name")
    description: str | None = Field(default=None, description="Updated description")
    status: UserStatus | None = Field(default=None, description="Updated user status")
    role: UserRole | None = Field(default=None, description="Updated user role")
    domain_name: str | None = Field(default=None, description="Updated domain name")
    allowed_client_ip: list[str] | None = Field(
        default=None, description="Updated allowed client IPs"
    )
    totp_activated: bool | None = Field(default=None, description="Updated TOTP activation status")
    resource_policy: str | None = Field(default=None, description="Updated resource policy name")
    sudo_session_enabled: bool | None = Field(
        default=None, description="Updated sudo session enabled flag"
    )
    main_access_key: str | None = Field(default=None, description="Updated main access key")
    container_uid: int | None = Field(default=None, description="Updated container UID")
    container_main_gid: int | None = Field(default=None, description="Updated container main GID")
    container_gids: list[int] | None = Field(
        default=None, description="Updated container additional GIDs"
    )
    group_ids: list[str] | None = Field(default=None, description="Updated group IDs")


class UserFilter(BaseRequestModel):
    """Filter criteria for searching users."""

    uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    email: StringFilter | None = Field(default=None, description="Filter by email")
    username: StringFilter | None = Field(default=None, description="Filter by username")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    status: list[UserStatus] | None = Field(default=None, description="Filter by user statuses")
    role: list[UserRole] | None = Field(default=None, description="Filter by user roles")


class UserOrder(BaseRequestModel):
    """Order specification for user search results."""

    field: UserOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchUsersRequest(BaseRequestModel):
    """Request body for searching users with filters, orders, and pagination."""

    filter: UserFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeleteUserRequest(BaseRequestModel):
    """Request to delete (soft-delete) a user."""

    user_id: UUID = Field(description="UUID of the user to delete")


class PurgeUserRequest(BaseRequestModel):
    """Request to purge (hard-delete) a user permanently."""

    user_id: UUID = Field(description="UUID of the user to purge")
    purge_shared_vfolders: bool = Field(
        default=False, description="Whether to purge shared virtual folders"
    )
    delegate_endpoint_ownership: bool = Field(
        default=False, description="Whether to delegate endpoint ownership"
    )

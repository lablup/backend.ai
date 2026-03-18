"""
Request DTOs for Resource Policy system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import DefaultForUnspecified

from .types import (
    KeypairResourcePolicyOrderField,
    OrderDirection,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
)

__all__ = (
    # Keypair
    "CreateKeypairResourcePolicyRequest",
    "DeleteKeypairResourcePolicyRequest",
    "KeypairResourcePolicyFilter",
    "KeypairResourcePolicyOrder",
    "SearchKeypairResourcePoliciesRequest",
    "UpdateKeypairResourcePolicyRequest",
    # User
    "CreateUserResourcePolicyRequest",
    "DeleteUserResourcePolicyRequest",
    "SearchUserResourcePoliciesRequest",
    "UpdateUserResourcePolicyRequest",
    "UserResourcePolicyFilter",
    "UserResourcePolicyOrder",
    # Project
    "CreateProjectResourcePolicyRequest",
    "DeleteProjectResourcePolicyRequest",
    "ProjectResourcePolicyFilter",
    "ProjectResourcePolicyOrder",
    "SearchProjectResourcePoliciesRequest",
    "UpdateProjectResourcePolicyRequest",
)


# ---- Keypair Resource Policy ----


class CreateKeypairResourcePolicyRequest(BaseRequestModel):
    """Request to create a keypair resource policy."""

    name: str = Field(description="Policy name")
    default_for_unspecified: DefaultForUnspecified = Field(
        default=DefaultForUnspecified.LIMITED,
        description="Default behavior for unspecified resource slots",
    )
    total_resource_slots: dict[str, Any] = Field(
        default_factory=dict, description="Total resource slots"
    )
    max_session_lifetime: int = Field(default=0, description="Max session lifetime in seconds")
    max_concurrent_sessions: int = Field(default=1, description="Max concurrent sessions")
    max_pending_session_count: int | None = Field(
        default=None, description="Max pending session count"
    )
    max_pending_session_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Max pending session resource slots"
    )
    max_concurrent_sftp_sessions: int = Field(default=1, description="Max concurrent SFTP sessions")
    max_containers_per_session: int = Field(default=1, description="Max containers per session")
    idle_timeout: int = Field(default=1800, description="Idle timeout in seconds")
    allowed_vfolder_hosts: dict[str, Any] = Field(
        default_factory=dict, description="Allowed vfolder hosts and permissions"
    )


class UpdateKeypairResourcePolicyRequest(BaseRequestModel):
    """Request to update a keypair resource policy."""

    default_for_unspecified: DefaultForUnspecified | Sentinel = Field(
        default=SENTINEL, description="Default behavior for unspecified resource slots"
    )
    total_resource_slots: dict[str, Any] | Sentinel = Field(
        default=SENTINEL, description="Total resource slots"
    )
    max_session_lifetime: int | Sentinel = Field(
        default=SENTINEL, description="Max session lifetime in seconds"
    )
    max_concurrent_sessions: int | Sentinel = Field(
        default=SENTINEL, description="Max concurrent sessions"
    )
    max_pending_session_count: int | None | Sentinel = Field(
        default=SENTINEL, description="Max pending session count"
    )
    max_pending_session_resource_slots: dict[str, Any] | None | Sentinel = Field(
        default=SENTINEL, description="Max pending session resource slots"
    )
    max_concurrent_sftp_sessions: int | Sentinel = Field(
        default=SENTINEL, description="Max concurrent SFTP sessions"
    )
    max_containers_per_session: int | Sentinel = Field(
        default=SENTINEL, description="Max containers per session"
    )
    idle_timeout: int | Sentinel = Field(default=SENTINEL, description="Idle timeout in seconds")
    allowed_vfolder_hosts: dict[str, Any] | Sentinel = Field(
        default=SENTINEL, description="Allowed vfolder hosts and permissions"
    )


class DeleteKeypairResourcePolicyRequest(BaseRequestModel):
    """Request to delete a keypair resource policy."""

    name: str = Field(description="Policy name to delete")


class KeypairResourcePolicyFilter(BaseRequestModel):
    """Filter for keypair resource policies."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class KeypairResourcePolicyOrder(BaseRequestModel):
    """Order specification for keypair resource policies."""

    field: KeypairResourcePolicyOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchKeypairResourcePoliciesRequest(BaseRequestModel):
    """Request body for searching keypair resource policies."""

    filter: KeypairResourcePolicyFilter | None = Field(
        default=None, description="Filter conditions"
    )
    order: list[KeypairResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# ---- User Resource Policy ----


class CreateUserResourcePolicyRequest(BaseRequestModel):
    """Request to create a user resource policy."""

    name: str = Field(description="Policy name")
    max_vfolder_count: int = Field(default=0, description="Max vfolder count")
    max_quota_scope_size: int = Field(default=0, description="Max quota scope size in bytes")
    max_session_count_per_model_session: int = Field(
        default=0, description="Max session count per model session"
    )
    max_customized_image_count: int = Field(default=3, description="Max customized image count")


class UpdateUserResourcePolicyRequest(BaseRequestModel):
    """Request to update a user resource policy."""

    max_vfolder_count: int | Sentinel = Field(default=SENTINEL, description="Max vfolder count")
    max_quota_scope_size: int | Sentinel = Field(
        default=SENTINEL, description="Max quota scope size in bytes"
    )
    max_session_count_per_model_session: int | Sentinel = Field(
        default=SENTINEL, description="Max session count per model session"
    )
    max_customized_image_count: int | Sentinel = Field(
        default=SENTINEL, description="Max customized image count"
    )


class DeleteUserResourcePolicyRequest(BaseRequestModel):
    """Request to delete a user resource policy."""

    name: str = Field(description="Policy name to delete")


class UserResourcePolicyFilter(BaseRequestModel):
    """Filter for user resource policies."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class UserResourcePolicyOrder(BaseRequestModel):
    """Order specification for user resource policies."""

    field: UserResourcePolicyOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchUserResourcePoliciesRequest(BaseRequestModel):
    """Request body for searching user resource policies."""

    filter: UserResourcePolicyFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# ---- Project Resource Policy ----


class CreateProjectResourcePolicyRequest(BaseRequestModel):
    """Request to create a project resource policy."""

    name: str = Field(description="Policy name")
    max_vfolder_count: int = Field(default=0, description="Max vfolder count")
    max_quota_scope_size: int = Field(default=0, description="Max quota scope size in bytes")
    max_network_count: int = Field(default=0, description="Max network count")


class UpdateProjectResourcePolicyRequest(BaseRequestModel):
    """Request to update a project resource policy."""

    max_vfolder_count: int | Sentinel = Field(default=SENTINEL, description="Max vfolder count")
    max_quota_scope_size: int | Sentinel = Field(
        default=SENTINEL, description="Max quota scope size in bytes"
    )
    max_network_count: int | Sentinel = Field(default=SENTINEL, description="Max network count")


class DeleteProjectResourcePolicyRequest(BaseRequestModel):
    """Request to delete a project resource policy."""

    name: str = Field(description="Policy name to delete")


class ProjectResourcePolicyFilter(BaseRequestModel):
    """Filter for project resource policies."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class ProjectResourcePolicyOrder(BaseRequestModel):
    """Order specification for project resource policies."""

    field: ProjectResourcePolicyOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchProjectResourcePoliciesRequest(BaseRequestModel):
    """Request body for searching project resource policies."""

    filter: ProjectResourcePolicyFilter | None = Field(
        default=None, description="Filter conditions"
    )
    order: list[ProjectResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")

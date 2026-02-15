"""
Response DTOs for Resource Policy system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import DefaultForUnspecified

__all__ = (
    # Keypair
    "CreateKeypairResourcePolicyResponse",
    "DeleteKeypairResourcePolicyResponse",
    "GetKeypairResourcePolicyResponse",
    "KeypairResourcePolicyDTO",
    "SearchKeypairResourcePoliciesResponse",
    "UpdateKeypairResourcePolicyResponse",
    # User
    "CreateUserResourcePolicyResponse",
    "DeleteUserResourcePolicyResponse",
    "GetUserResourcePolicyResponse",
    "SearchUserResourcePoliciesResponse",
    "UpdateUserResourcePolicyResponse",
    "UserResourcePolicyDTO",
    # Project
    "CreateProjectResourcePolicyResponse",
    "DeleteProjectResourcePolicyResponse",
    "GetProjectResourcePolicyResponse",
    "ProjectResourcePolicyDTO",
    "SearchProjectResourcePoliciesResponse",
    "UpdateProjectResourcePolicyResponse",
    # Common
    "PaginationInfo",
)


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


# ---- Keypair Resource Policy ----


class KeypairResourcePolicyDTO(BaseModel):
    """DTO for keypair resource policy data."""

    name: str = Field(description="Policy name")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    default_for_unspecified: DefaultForUnspecified = Field(
        description="Default behavior for unspecified resource slots"
    )
    total_resource_slots: dict[str, Any] = Field(description="Total resource slots")
    max_session_lifetime: int = Field(description="Max session lifetime in seconds")
    max_concurrent_sessions: int = Field(description="Max concurrent sessions")
    max_pending_session_count: int | None = Field(description="Max pending session count")
    max_pending_session_resource_slots: dict[str, Any] | None = Field(
        description="Max pending session resource slots"
    )
    max_concurrent_sftp_sessions: int = Field(description="Max concurrent SFTP sessions")
    max_containers_per_session: int = Field(description="Max containers per session")
    idle_timeout: int = Field(description="Idle timeout in seconds")
    allowed_vfolder_hosts: dict[str, Any] = Field(
        description="Allowed vfolder hosts and permissions"
    )


class CreateKeypairResourcePolicyResponse(BaseResponseModel):
    """Response for creating a keypair resource policy."""

    item: KeypairResourcePolicyDTO = Field(description="Created policy")


class GetKeypairResourcePolicyResponse(BaseResponseModel):
    """Response for getting a keypair resource policy."""

    item: KeypairResourcePolicyDTO = Field(description="Policy data")


class UpdateKeypairResourcePolicyResponse(BaseResponseModel):
    """Response for updating a keypair resource policy."""

    item: KeypairResourcePolicyDTO = Field(description="Updated policy")


class DeleteKeypairResourcePolicyResponse(BaseResponseModel):
    """Response for deleting a keypair resource policy."""

    deleted: bool = Field(description="Whether the policy was deleted")


class SearchKeypairResourcePoliciesResponse(BaseResponseModel):
    """Response for searching keypair resource policies."""

    items: list[KeypairResourcePolicyDTO] = Field(description="List of policies")
    pagination: PaginationInfo = Field(description="Pagination information")


# ---- User Resource Policy ----


class UserResourcePolicyDTO(BaseModel):
    """DTO for user resource policy data."""

    name: str = Field(description="Policy name")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    max_vfolder_count: int = Field(description="Max vfolder count")
    max_quota_scope_size: int = Field(description="Max quota scope size in bytes")
    max_session_count_per_model_session: int = Field(
        description="Max session count per model session"
    )
    max_customized_image_count: int = Field(description="Max customized image count")


class CreateUserResourcePolicyResponse(BaseResponseModel):
    """Response for creating a user resource policy."""

    item: UserResourcePolicyDTO = Field(description="Created policy")


class GetUserResourcePolicyResponse(BaseResponseModel):
    """Response for getting a user resource policy."""

    item: UserResourcePolicyDTO = Field(description="Policy data")


class UpdateUserResourcePolicyResponse(BaseResponseModel):
    """Response for updating a user resource policy."""

    item: UserResourcePolicyDTO = Field(description="Updated policy")


class DeleteUserResourcePolicyResponse(BaseResponseModel):
    """Response for deleting a user resource policy."""

    deleted: bool = Field(description="Whether the policy was deleted")


class SearchUserResourcePoliciesResponse(BaseResponseModel):
    """Response for searching user resource policies."""

    items: list[UserResourcePolicyDTO] = Field(description="List of policies")
    pagination: PaginationInfo = Field(description="Pagination information")


# ---- Project Resource Policy ----


class ProjectResourcePolicyDTO(BaseModel):
    """DTO for project resource policy data."""

    name: str = Field(description="Policy name")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    max_vfolder_count: int = Field(description="Max vfolder count")
    max_quota_scope_size: int = Field(description="Max quota scope size in bytes")
    max_network_count: int = Field(description="Max network count")


class CreateProjectResourcePolicyResponse(BaseResponseModel):
    """Response for creating a project resource policy."""

    item: ProjectResourcePolicyDTO = Field(description="Created policy")


class GetProjectResourcePolicyResponse(BaseResponseModel):
    """Response for getting a project resource policy."""

    item: ProjectResourcePolicyDTO = Field(description="Policy data")


class UpdateProjectResourcePolicyResponse(BaseResponseModel):
    """Response for updating a project resource policy."""

    item: ProjectResourcePolicyDTO = Field(description="Updated policy")


class DeleteProjectResourcePolicyResponse(BaseResponseModel):
    """Response for deleting a project resource policy."""

    deleted: bool = Field(description="Whether the policy was deleted")


class SearchProjectResourcePoliciesResponse(BaseResponseModel):
    """Response for searching project resource policies."""

    items: list[ProjectResourcePolicyDTO] = Field(description="List of policies")
    pagination: PaginationInfo = Field(description="Pagination information")

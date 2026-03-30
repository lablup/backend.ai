"""
Response DTOs for resource policy DTO v2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
    ResourceLimitEntryInfo,
    VFolderHostPermissionEntryInfo,
)

from .types import DefaultForUnspecified

__all__ = (
    "CreateKeypairResourcePolicyPayload",
    "CreateProjectResourcePolicyPayload",
    "CreateUserResourcePolicyPayload",
    "DeleteKeypairResourcePolicyPayload",
    "DeleteProjectResourcePolicyPayload",
    "DeleteUserResourcePolicyPayload",
    "KeypairResourcePolicyNode",
    "ProjectResourcePolicyNode",
    "UpdateKeypairResourcePolicyPayload",
    "UpdateProjectResourcePolicyPayload",
    "UpdateUserResourcePolicyPayload",
    "UserResourcePolicyNode",
)


class KeypairResourcePolicyNode(BaseResponseModel):
    """Node model representing a keypair resource policy entity."""

    id: str = Field(description="Policy name (primary key).")
    name: str = Field(description="Unique name of the keypair resource policy.")
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the policy was created.",
    )
    default_for_unspecified: DefaultForUnspecified = Field(
        description="Default resource allocation for unspecified resource slots.",
    )
    total_resource_slots: list[ResourceLimitEntryInfo] = Field(
        description="Total resource slot limits for sessions using this policy.",
    )
    max_session_lifetime: int = Field(
        description="Maximum lifetime of a session in seconds.",
    )
    max_concurrent_sessions: int = Field(
        description="Maximum number of concurrent sessions allowed.",
    )
    max_pending_session_count: int | None = Field(
        default=None,
        description="Maximum number of sessions in pending state. Null means unlimited.",
    )
    max_pending_session_resource_slots: list[ResourceLimitEntryInfo] | None = Field(
        default=None,
        description="Maximum resource slots occupied by pending sessions. Null means unlimited.",
    )
    max_concurrent_sftp_sessions: int = Field(
        description="Maximum number of concurrent SFTP sessions allowed.",
    )
    max_containers_per_session: int = Field(
        description="Maximum number of containers allowed per session.",
    )
    idle_timeout: int = Field(
        description="Idle timeout for sessions in seconds.",
    )
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInfo] = Field(
        description="Allowed vfolder host permissions for this policy.",
    )


class CreateKeypairResourcePolicyPayload(BaseResponseModel):
    """Payload for keypair resource policy creation mutation result."""

    keypair_resource_policy: KeypairResourcePolicyNode = Field(
        description="Created keypair resource policy."
    )


class UpdateKeypairResourcePolicyPayload(BaseResponseModel):
    """Payload for keypair resource policy update mutation result."""

    keypair_resource_policy: KeypairResourcePolicyNode = Field(
        description="Updated keypair resource policy."
    )


class DeleteKeypairResourcePolicyPayload(BaseResponseModel):
    """Payload for keypair resource policy deletion mutation result."""

    name: str = Field(description="Name of the deleted keypair resource policy.")


class UserResourcePolicyNode(BaseResponseModel):
    """Node model representing a user resource policy entity."""

    id: str = Field(description="Policy name (primary key).")
    name: str = Field(description="Unique name of the user resource policy.")
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the policy was created.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a user can create.",
    )
    max_quota_scope_size: BinarySizeInfo = Field(
        description="Maximum quota scope size.",
    )
    max_session_count_per_model_session: int = Field(
        description="Maximum number of sessions allowed per model session.",
    )
    max_customized_image_count: int = Field(
        description="Maximum number of customized images a user can create.",
    )


class CreateUserResourcePolicyPayload(BaseResponseModel):
    """Payload for user resource policy creation mutation result."""

    user_resource_policy: UserResourcePolicyNode = Field(
        description="Created user resource policy."
    )


class UpdateUserResourcePolicyPayload(BaseResponseModel):
    """Payload for user resource policy update mutation result."""

    user_resource_policy: UserResourcePolicyNode = Field(
        description="Updated user resource policy."
    )


class DeleteUserResourcePolicyPayload(BaseResponseModel):
    """Payload for user resource policy deletion mutation result."""

    name: str = Field(description="Name of the deleted user resource policy.")


class ProjectResourcePolicyNode(BaseResponseModel):
    """Node model representing a project resource policy entity."""

    id: str = Field(description="Policy name (primary key).")
    name: str = Field(description="Unique name of the project resource policy.")
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the policy was created.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a project can have.",
    )
    max_quota_scope_size: BinarySizeInfo = Field(
        description="Maximum quota scope size.",
    )
    max_network_count: int = Field(
        description="Maximum number of networks a project can create.",
    )


class CreateProjectResourcePolicyPayload(BaseResponseModel):
    """Payload for project resource policy creation mutation result."""

    project_resource_policy: ProjectResourcePolicyNode = Field(
        description="Created project resource policy."
    )


class UpdateProjectResourcePolicyPayload(BaseResponseModel):
    """Payload for project resource policy update mutation result."""

    project_resource_policy: ProjectResourcePolicyNode = Field(
        description="Updated project resource policy."
    )


class DeleteProjectResourcePolicyPayload(BaseResponseModel):
    """Payload for project resource policy deletion mutation result."""

    name: str = Field(description="Name of the deleted project resource policy.")


class SearchKeypairResourcePoliciesPayload(BaseResponseModel):
    """Payload for keypair resource policy search results."""

    items: list[KeypairResourcePolicyNode] = Field(description="List of keypair resource policies.")
    total_count: int = Field(description="Total number of matching policies.")


class SearchUserResourcePoliciesPayload(BaseResponseModel):
    """Payload for user resource policy search results."""

    items: list[UserResourcePolicyNode] = Field(description="List of user resource policies.")
    total_count: int = Field(description="Total number of matching policies.")


class SearchProjectResourcePoliciesPayload(BaseResponseModel):
    """Payload for project resource policy search results."""

    items: list[ProjectResourcePolicyNode] = Field(description="List of project resource policies.")
    total_count: int = Field(description="Total number of matching policies.")

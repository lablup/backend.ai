"""
Request DTOs for resource policy DTO v2.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, IntFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    OrderDirection,
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInput,
)

from .types import (
    DefaultForUnspecified,
    KeypairResourcePolicyOrderField,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
)

__all__ = (
    "AdminSearchKeypairResourcePoliciesInput",
    "AdminSearchProjectResourcePoliciesInput",
    "AdminSearchUserResourcePoliciesInput",
    "KeypairResourcePolicyFilter",
    "UserResourcePolicyFilter",
    "ProjectResourcePolicyFilter",
    "KeypairResourcePolicyOrder",
    "UserResourcePolicyOrder",
    "ProjectResourcePolicyOrder",
    "CreateKeypairResourcePolicyInput",
    "CreateProjectResourcePolicyInput",
    "CreateUserResourcePolicyInput",
    "DeleteKeypairResourcePolicyInput",
    "DeleteProjectResourcePolicyInput",
    "DeleteUserResourcePolicyInput",
    "UpdateKeypairResourcePolicyInput",
    "UpdateProjectResourcePolicyInput",
    "UpdateUserResourcePolicyInput",
)


class CreateKeypairResourcePolicyInput(BaseRequestModel):
    """Input for creating a new keypair resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    default_for_unspecified: DefaultForUnspecified = Field(
        description="Default resource allocation for unspecified resource slots.",
    )
    total_resource_slots: list[ResourceSlotEntryInput] = Field(
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
    max_pending_session_resource_slots: list[ResourceSlotEntryInput] | None = Field(
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
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInput] = Field(
        description="Allowed vfolder host permissions for this policy.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateKeypairResourcePolicyInput(BaseRequestModel):
    """Input for updating a keypair resource policy. All fields optional for partial update."""

    default_for_unspecified: DefaultForUnspecified | None = Field(
        default=None,
        description="Updated default resource allocation. Leave null to keep existing value.",
    )
    total_resource_slots: list[ResourceSlotEntryInput] | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated resource slot limits. Set to null to clear.",
    )
    max_session_lifetime: int | None = Field(
        default=None,
        description="Updated maximum session lifetime in seconds. Leave null to keep existing.",
    )
    max_concurrent_sessions: int | None = Field(
        default=None,
        description="Updated maximum concurrent sessions. Leave null to keep existing.",
    )
    max_pending_session_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max pending sessions. Set to null to clear.",
    )
    max_pending_session_resource_slots: list[ResourceSlotEntryInput] | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max pending session resource slots. Set to null to clear.",
    )
    max_concurrent_sftp_sessions: int | None = Field(
        default=None,
        description="Updated max concurrent SFTP sessions. Leave null to keep existing.",
    )
    max_containers_per_session: int | None = Field(
        default=None,
        description="Updated max containers per session. Leave null to keep existing.",
    )
    idle_timeout: int | None = Field(
        default=None,
        description="Updated idle timeout in seconds. Leave null to keep existing.",
    )
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInput] | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated vfolder host permissions. Set to null to clear.",
    )


class DeleteKeypairResourcePolicyInput(BaseRequestModel):
    """Input for deleting a keypair resource policy."""

    name: str = Field(description="Name of the keypair resource policy to delete.")


class CreateUserResourcePolicyInput(BaseRequestModel):
    """Input for creating a new user resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a user can create.",
    )
    max_quota_scope_size: BinarySizeInput = Field(
        description="Maximum quota scope size (e.g., '1g', '536870912').",
    )
    max_session_count_per_model_session: int = Field(
        description="Maximum number of sessions allowed per model session.",
    )
    max_customized_image_count: int = Field(
        description="Maximum number of customized images a user can create.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateUserResourcePolicyInput(BaseRequestModel):
    """Input for updating a user resource policy. All fields optional for partial update."""

    max_vfolder_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max vfolder count. Use SENTINEL to clear, null to keep existing.",
    )
    max_quota_scope_size: BinarySizeInput | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max quota scope size. Use SENTINEL to clear, null to keep existing.",
    )
    max_session_count_per_model_session: int | None = Field(
        default=None,
        description="Updated max sessions per model session. Leave null to keep existing.",
    )
    max_customized_image_count: int | None = Field(
        default=None,
        description="Updated max customized image count. Leave null to keep existing.",
    )


class DeleteUserResourcePolicyInput(BaseRequestModel):
    """Input for deleting a user resource policy."""

    name: str = Field(description="Name of the user resource policy to delete.")


class CreateProjectResourcePolicyInput(BaseRequestModel):
    """Input for creating a new project resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a project can have.",
    )
    max_quota_scope_size: BinarySizeInput = Field(
        description="Maximum quota scope size (e.g., '1g', '536870912').",
    )
    max_network_count: int = Field(
        description="Maximum number of networks a project can create.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateProjectResourcePolicyInput(BaseRequestModel):
    """Input for updating a project resource policy. All fields optional for partial update."""

    max_vfolder_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max vfolder count. Use SENTINEL to clear, null to keep existing.",
    )
    max_quota_scope_size: BinarySizeInput | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max quota scope size. Use SENTINEL to clear, null to keep existing.",
    )
    max_network_count: int | None = Field(
        default=None,
        description="Updated max network count. Leave null to keep existing.",
    )


class DeleteProjectResourcePolicyInput(BaseRequestModel):
    """Input for deleting a project resource policy."""

    name: str = Field(description="Name of the project resource policy to delete.")


# ── Filter & Order DTOs ──


class KeypairResourcePolicyFilter(BaseRequestModel):
    """Filter for keypair resource policy search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    max_session_lifetime: IntFilter | None = Field(
        default=None, description="Filter by max session lifetime."
    )
    max_concurrent_sessions: IntFilter | None = Field(
        default=None, description="Filter by max concurrent sessions."
    )
    max_containers_per_session: IntFilter | None = Field(
        default=None, description="Filter by max containers per session."
    )
    idle_timeout: IntFilter | None = Field(default=None, description="Filter by idle timeout.")
    max_concurrent_sftp_sessions: IntFilter | None = Field(
        default=None, description="Filter by max concurrent SFTP sessions."
    )
    max_pending_session_count: IntFilter | None = Field(
        default=None, description="Filter by max pending session count."
    )


class UserResourcePolicyFilter(BaseRequestModel):
    """Filter for user resource policy search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    max_vfolder_count: IntFilter | None = Field(
        default=None, description="Filter by max vfolder count."
    )
    max_quota_scope_size: IntFilter | None = Field(
        default=None, description="Filter by max quota scope size."
    )
    max_session_count_per_model_session: IntFilter | None = Field(
        default=None, description="Filter by max sessions per model session."
    )
    max_customized_image_count: IntFilter | None = Field(
        default=None, description="Filter by max customized image count."
    )


class ProjectResourcePolicyFilter(BaseRequestModel):
    """Filter for project resource policy search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    max_vfolder_count: IntFilter | None = Field(
        default=None, description="Filter by max vfolder count."
    )
    max_quota_scope_size: IntFilter | None = Field(
        default=None, description="Filter by max quota scope size."
    )
    max_network_count: IntFilter | None = Field(
        default=None, description="Filter by max network count."
    )


class KeypairResourcePolicyOrder(BaseRequestModel):
    """Order specification for keypair resource policy search."""

    field: KeypairResourcePolicyOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


class UserResourcePolicyOrder(BaseRequestModel):
    """Order specification for user resource policy search."""

    field: UserResourcePolicyOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


class ProjectResourcePolicyOrder(BaseRequestModel):
    """Order specification for project resource policy search."""

    field: ProjectResourcePolicyOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


# ── Search Input DTOs ──


class AdminSearchKeypairResourcePoliciesInput(BaseRequestModel):
    """Input for admin search of keypair resource policies."""

    filter: KeypairResourcePolicyFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[KeypairResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AdminSearchUserResourcePoliciesInput(BaseRequestModel):
    """Input for admin search of user resource policies."""

    filter: UserResourcePolicyFilter | None = Field(default=None, description="Filter conditions.")
    order: list[UserResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AdminSearchProjectResourcePoliciesInput(BaseRequestModel):
    """Input for admin search of project resource policies."""

    filter: ProjectResourcePolicyFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[ProjectResourcePolicyOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")

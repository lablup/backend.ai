"""
Request DTOs for resource policy DTO v2.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    IntFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    NonEmptyList,
    OrderDirection,
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.tristate.unset import UNSET, Unset

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
    "PartialBulkPurgeKeypairResourcePoliciesInput",
    "PartialBulkPurgeProjectResourcePoliciesInput",
    "PartialBulkPurgeUserResourcePoliciesInput",
    "PartialBulkUpdateKeypairResourcePoliciesInput",
    "PartialBulkUpdateKeypairResourcePolicyItemInput",
    "PartialBulkUpdateProjectResourcePoliciesInput",
    "PartialBulkUpdateProjectResourcePolicyItemInput",
    "PartialBulkUpdateUserResourcePoliciesInput",
    "PartialBulkUpdateUserResourcePolicyItemInput",
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
    max_priority: int | None = Field(
        default=None,
        description="Highest scheduling priority a session may declare. Null means uncapped.",
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

    default_for_unspecified: DefaultForUnspecified | None | Unset = Field(
        default=UNSET,
        description="Updated default resource allocation. Omit to leave unchanged.",
    )
    total_resource_slots: list[ResourceSlotEntryInput] | None | Unset = Field(
        default=UNSET,
        description="Updated resource slot limits. Omit to leave unchanged.",
    )
    max_session_lifetime: int | None | Unset = Field(
        default=UNSET,
        description="Updated maximum session lifetime in seconds. Omit to leave unchanged.",
    )
    max_concurrent_sessions: int | None | Unset = Field(
        default=UNSET,
        description="Updated maximum concurrent sessions. Omit to leave unchanged.",
    )
    max_pending_session_count: int | None | Unset = Field(
        default=UNSET,
        description="Updated max pending sessions. Omit to leave unchanged; null clears.",
    )
    max_priority: int | None | Unset = Field(
        default=UNSET,
        description="Updated max priority. Omit to leave unchanged; null clears.",
    )
    max_pending_session_resource_slots: list[ResourceSlotEntryInput] | None | Unset = Field(
        default=UNSET,
        description=(
            "Updated max pending session resource slots. Omit to leave unchanged; null clears."
        ),
    )
    max_concurrent_sftp_sessions: int | None | Unset = Field(
        default=UNSET,
        description="Updated max concurrent SFTP sessions. Omit to leave unchanged.",
    )
    max_containers_per_session: int | None | Unset = Field(
        default=UNSET,
        description="Updated max containers per session. Omit to leave unchanged.",
    )
    idle_timeout: int | None | Unset = Field(
        default=UNSET,
        description="Updated idle timeout in seconds. Omit to leave unchanged.",
    )
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInput] | None | Unset = Field(
        default=UNSET,
        description="Updated vfolder host permissions. Omit to leave unchanged.",
    )


class DeleteKeypairResourcePolicyInput(BaseRequestModel):
    """Input for deleting a keypair resource policy."""

    name: str = Field(description="Name of the keypair resource policy to delete.")


class PartialBulkUpdateKeypairResourcePolicyItemInput(BaseRequestModel):
    """One keypair resource policy of a partial bulk update and the fields to update on it."""

    id: UUID = Field(description="ID of the keypair resource policy to update.")
    input: UpdateKeypairResourcePolicyInput = Field(description="Fields to update on the policy.")


class PartialBulkUpdateKeypairResourcePoliciesInput(BaseRequestModel):
    """Input for updating several keypair resource policies, each answered for separately."""

    items: NonEmptyList[PartialBulkUpdateKeypairResourcePolicyItemInput] = Field(
        description="The keypair resource policies to update, each with its fields."
    )


class PartialBulkPurgeKeypairResourcePoliciesInput(BaseRequestModel):
    """Input for purging several keypair resource policies, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the keypair resource policies to purge.")


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
    max_concurrent_logins: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Maximum number of concurrent authenticated login sessions per user."
            " Null means unlimited. Must be >= 1 when set."
            " Distinct from keypair_resource_policies.max_concurrent_sessions which caps compute sessions."
        ),
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

    max_vfolder_count: int | None | Unset = Field(
        default=UNSET,
        description="Updated max vfolder count. Omit to leave unchanged.",
    )
    max_concurrent_logins: int | None | Unset = Field(
        default=UNSET,
        ge=1,
        description=(
            "Updated maximum number of concurrent authenticated login sessions per user."
            " Omit to leave unchanged; null clears (unlimited). Must be >= 1 when set."
            " Distinct from keypair_resource_policies.max_concurrent_sessions which caps compute sessions."
        ),
    )
    max_quota_scope_size: BinarySizeInput | None | Unset = Field(
        default=UNSET,
        description="Updated max quota scope size. Omit to leave unchanged.",
    )
    max_session_count_per_model_session: int | None | Unset = Field(
        default=UNSET,
        description="Updated max sessions per model session. Omit to leave unchanged.",
    )
    max_customized_image_count: int | None | Unset = Field(
        default=UNSET,
        description="Updated max customized image count. Omit to leave unchanged.",
    )


class DeleteUserResourcePolicyInput(BaseRequestModel):
    """Input for deleting a user resource policy."""

    name: str = Field(description="Name of the user resource policy to delete.")


class PartialBulkUpdateUserResourcePolicyItemInput(BaseRequestModel):
    """One user resource policy of a partial bulk update and the fields to update on it."""

    id: UUID = Field(description="ID of the user resource policy to update.")
    input: UpdateUserResourcePolicyInput = Field(description="Fields to update on the policy.")


class PartialBulkUpdateUserResourcePoliciesInput(BaseRequestModel):
    """Input for updating several user resource policies, each answered for separately."""

    items: NonEmptyList[PartialBulkUpdateUserResourcePolicyItemInput] = Field(
        description="The user resource policies to update, each with its fields."
    )


class PartialBulkPurgeUserResourcePoliciesInput(BaseRequestModel):
    """Input for purging several user resource policies, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the user resource policies to purge.")


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

    max_vfolder_count: int | None | Unset = Field(
        default=UNSET,
        description="Updated max vfolder count. Omit to leave unchanged.",
    )
    max_quota_scope_size: BinarySizeInput | None | Unset = Field(
        default=UNSET,
        description="Updated max quota scope size. Omit to leave unchanged.",
    )
    max_network_count: int | None | Unset = Field(
        default=UNSET,
        description="Updated max network count. Omit to leave unchanged.",
    )


class DeleteProjectResourcePolicyInput(BaseRequestModel):
    """Input for deleting a project resource policy."""

    name: str = Field(description="Name of the project resource policy to delete.")


class PartialBulkUpdateProjectResourcePolicyItemInput(BaseRequestModel):
    """One project resource policy of a partial bulk update and the fields to update on it."""

    id: UUID = Field(description="ID of the project resource policy to update.")
    input: UpdateProjectResourcePolicyInput = Field(description="Fields to update on the policy.")


class PartialBulkUpdateProjectResourcePoliciesInput(BaseRequestModel):
    """Input for updating several project resource policies, each answered for separately."""

    items: NonEmptyList[PartialBulkUpdateProjectResourcePolicyItemInput] = Field(
        description="The project resource policies to update, each with its fields."
    )


class PartialBulkPurgeProjectResourcePoliciesInput(BaseRequestModel):
    """Input for purging several project resource policies, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the project resource policies to purge.")


# ── Filter & Order DTOs ──


class KeypairResourcePolicyKeypairNestedFilter(BaseRequestModel):
    """Nested filter for keypairs attached to a keypair resource policy.

    Filters policies that have at least one keypair matching all specified
    conditions.
    """

    user_id: UUIDFilter | None = Field(
        default=None, description="Filter by the UUID of the keypair owner."
    )


class KeypairResourcePolicyFilter(BaseRequestModel):
    """Filter for keypair resource policy search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    keypair: KeypairResourcePolicyKeypairNestedFilter | None = Field(
        default=None,
        description=(
            "Nested filter on keypairs assigned to this policy. "
            "Matches policies linked to at least one keypair satisfying the conditions."
        ),
    )
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
    max_priority: IntFilter | None = Field(
        default=None, description="Filter by max scheduling priority."
    )
    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by keypair resource policy ID.",
    )
    AND: list[Self] | None = Field(default=None, description="Match all of the given sub-filters.")
    OR: list[Self] | None = Field(default=None, description="Match any of the given sub-filters.")
    NOT: list[Self] | None = Field(default=None, description="Negate the given sub-filters.")


class UserResourcePolicyFilter(BaseRequestModel):
    """Filter for user resource policy search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    max_vfolder_count: IntFilter | None = Field(
        default=None, description="Filter by max vfolder count."
    )
    max_concurrent_logins: IntFilter | None = Field(
        default=None, description="Filter by max concurrent logins."
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
    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by user resource policy ID.",
    )
    AND: list[Self] | None = Field(default=None, description="Match all of the given sub-filters.")
    OR: list[Self] | None = Field(default=None, description="Match any of the given sub-filters.")
    NOT: list[Self] | None = Field(default=None, description="Negate the given sub-filters.")


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
    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by project resource policy ID.",
    )
    AND: list[Self] | None = Field(default=None, description="Match all of the given sub-filters.")
    OR: list[Self] | None = Field(default=None, description="Match any of the given sub-filters.")
    NOT: list[Self] | None = Field(default=None, description="Negate the given sub-filters.")


KeypairResourcePolicyFilter.model_rebuild()
UserResourcePolicyFilter.model_rebuild()
ProjectResourcePolicyFilter.model_rebuild()


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

"""
Response DTOs for RBAC DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.types import EntityType

from .types import (
    OperationTypeDTO,
    PermissionBitDTO,
    RoleSourceDTO,
    RoleStatusDTO,
)

__all__ = (
    "AdminSearchPermissionsPayload",
    "SearchRoleAssignmentsPayload",
    "AdminSearchRolesPayload",
    "BulkAddRolePermissionFailureInfo",
    "BulkAddRolePermissionsPayload",
    "BulkAssignRoleFailureInfo",
    "BulkAssignRoleResultPayload",
    "BulkRemoveRolePermissionFailureInfo",
    "BulkRemoveRolePermissionsPayload",
    "BulkRevokeRoleFailureInfo",
    "BulkRevokeRoleResultPayload",
    "CreateRolePayload",
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "EntityActionInfo",
    "EntityOperationCombinationInfo",
    "OperationInfo",
    "PermissionNode",
    "PurgeRolePayload",
    "ReplaceRolePermissionFailureInfo",
    "ReplaceRolePermissionsPayload",
    "RoleAssignmentNode",
    "RoleNode",
    "ScopeEntityCombinationInfo",
    "ScopeEntityOperationCombinationInfo",
    "UpdateRolePayload",
)


class RoleNode(BaseResponseModel):
    """Node model representing a role entity."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")
    source: RoleSourceDTO = Field(description="Role source")
    status: RoleStatusDTO = Field(description="Role status")
    auto_assign: bool = Field(
        default=False,
        description=(
            "When true, the role is automatically granted to a user when the user is added "
            "to a scope this role is registered in."
        ),
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    deleted_at: datetime | None = Field(default=None, description="Deletion timestamp")
    scope_type: EntityType = Field(description="Type of the scope the role belongs to")
    scope_id: UUID = Field(description="ID of the scope the role belongs to")


class CreateRolePayload(BaseResponseModel):
    """Payload for role creation mutation result."""

    role: RoleNode = Field(description="Created role")


class UpdateRolePayload(BaseResponseModel):
    """Payload for role update mutation result."""

    role: RoleNode = Field(description="Updated role")


class DeleteRolePayload(BaseResponseModel):
    """Payload for role soft-deletion mutation result."""

    id: UUID = Field(description="ID of the deleted role")


class PurgeRolePayload(BaseResponseModel):
    """Payload for role purge mutation result."""

    id: UUID = Field(description="ID of the purged role")


class DeletePermissionPayload(BaseResponseModel):
    """Payload for permission deletion mutation result."""

    id: UUID = Field(description="ID of the deleted permission")


class RoleAssignmentNode(BaseResponseModel):
    """Node representing a user-role assignment."""

    id: UUID = Field(description="Assignment ID")
    user_id: UUID = Field(description="Assigned user ID")
    role_id: UUID = Field(description="Assigned role ID")
    granted_by: UUID | None = Field(default=None, description="User who granted the assignment")
    granted_at: datetime = Field(description="Timestamp when the assignment was created")


class BulkAssignRoleFailureInfo(BaseResponseModel):
    """Failure detail for a single user in a bulk role assignment."""

    user_id: UUID = Field(description="UUID of the user that failed")
    message: str = Field(description="Error message describing the failure")


class BulkRevokeRoleFailureInfo(BaseResponseModel):
    """Failure detail for a single user in a bulk role revocation."""

    user_id: UUID = Field(description="UUID of the user that failed")
    message: str = Field(description="Error message describing the failure")


class BulkAssignRoleResultPayload(BaseResponseModel):
    """Result payload for bulk role assignment."""

    assigned: list[RoleAssignmentNode] = Field(
        default_factory=list, description="Successfully created role assignments"
    )
    failed: list[BulkAssignRoleFailureInfo] = Field(
        default_factory=list, description="Users that failed to be assigned"
    )


class BulkRevokeRoleResultPayload(BaseResponseModel):
    """Result payload for bulk role revocation."""

    revoked: list[RoleAssignmentNode] = Field(
        default_factory=list, description="Successfully revoked role assignments"
    )
    failed: list[BulkRevokeRoleFailureInfo] = Field(
        default_factory=list, description="Users that failed to be revoked"
    )


class BulkAddRolePermissionFailureInfo(BaseResponseModel):
    """Failure detail for a single permission entry in bulk role-permission insertion."""

    role_id: UUID = Field(description="Role ID of the failed entry")
    entity_type: str = Field(description="Entity element type of the failed entry")
    operation: str = Field(description="Operation type of the failed entry")
    message: str = Field(description="Error message describing the failure")


class BulkRemoveRolePermissionFailureInfo(BaseResponseModel):
    """Failure detail for a single permission ID in bulk role-permission deletion."""

    permission_id: UUID = Field(description="Permission row ID that failed to delete")
    message: str = Field(description="Error message describing the failure")


class ReplaceRolePermissionFailureInfo(BaseResponseModel):
    """Failure detail for a single permission entry in replace operation."""

    role_id: UUID = Field(description="Role ID of the failed entry")
    entity_type: str = Field(description="Entity element type of the failed entry")
    operation: str = Field(description="Operation type of the failed entry")
    message: str = Field(description="Error message describing the failure")


class BulkAddRolePermissionsPayload(BaseResponseModel):
    """Result payload for bulk role-permission insertion."""

    items: list[PermissionNode] = Field(
        default_factory=list, description="Successfully inserted permission rows"
    )
    failed: list[BulkAddRolePermissionFailureInfo] = Field(
        default_factory=list, description="Permission entries that failed to insert"
    )


class BulkRemoveRolePermissionsPayload(BaseResponseModel):
    """Result payload for bulk role-permission deletion."""

    items: list[PermissionNode] = Field(
        default_factory=list, description="Successfully deleted permission rows"
    )
    failed: list[BulkRemoveRolePermissionFailureInfo] = Field(
        default_factory=list, description="Permission IDs that failed to delete"
    )


class ReplaceRolePermissionsPayload(BaseResponseModel):
    """Result payload for replacing a role's entire scoped-permission set.

    ``items`` contains the new rows that became the role's permission set;
    pre-existing rows wiped before the insert are not echoed back.
    """

    items: list[PermissionNode] = Field(
        default_factory=list, description="Permission rows that make up the new set"
    )
    failed: list[ReplaceRolePermissionFailureInfo] = Field(
        default_factory=list, description="Permission entries that failed to insert"
    )


class PermissionNode(BaseResponseModel):
    """Node representing a scoped RBAC permission."""

    id: UUID = Field(description="Permission ID")
    role_id: UUID = Field(description="Role this permission belongs to")
    entity_type: EntityType = Field(description="Entity element type")
    permission: PermissionBitDTO = Field(description="The permission bit the row holds")
    operation: OperationTypeDTO = Field(
        description="Deprecated: use `permission`. The same bit named as an action.",
        deprecated=True,
    )
    created_at: datetime = Field(description="Creation timestamp")


class AdminSearchRolesPayload(BaseResponseModel):
    """Paginated result for role search."""

    items: list[RoleNode] = Field(description="List of role nodes.")
    total_count: int = Field(description="Total number of roles matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class AdminSearchPermissionsPayload(BaseResponseModel):
    """Paginated result for permission search."""

    items: list[PermissionNode] = Field(description="List of permission nodes.")
    total_count: int = Field(description="Total number of permissions matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class SearchRoleAssignmentsPayload(BaseResponseModel):
    """Paginated result for role assignment search."""

    items: list[RoleAssignmentNode] = Field(description="List of role assignment nodes.")
    total_count: int = Field(description="Total number of assignments matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class ScopeEntityCombinationInfo(BaseResponseModel):
    """Valid scope-entity type combination for RBAC permissions."""

    scope_type: EntityType = Field(description="Scope element type")
    valid_entity_types: list[EntityType] = Field(
        description="Valid entity types for this scope type"
    )


class OperationInfo(BaseResponseModel):
    """Information about a single RBAC operation."""

    operation: str = Field(description="Operation name")
    description: str = Field(description="Human-readable description")
    required_permission: OperationTypeDTO = Field(description="Required RBAC permission")


class EntityOperationCombinationInfo(BaseResponseModel):
    """Valid entity-operation combinations for RBAC actions."""

    entity_type: EntityType = Field(description="Entity element type")
    operations: list[OperationInfo] = Field(description="Valid operations for this entity")


class EntityActionInfo(BaseResponseModel):
    """Entity type with its allowed actions within a specific scope."""

    entity_type: EntityType = Field(description="Entity element type")
    actions: list[OperationInfo] = Field(
        description="Valid operations for this entity in the given scope"
    )


class ScopeEntityOperationCombinationInfo(BaseResponseModel):
    """Complete scope-entity-operation combination for RBAC permission matrix."""

    scope_type: EntityType = Field(description="Scope element type")
    entities: list[EntityActionInfo] = Field(
        description="Entities and their valid operations within this scope"
    )

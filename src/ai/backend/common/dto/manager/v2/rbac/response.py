"""
Response DTOs for RBAC DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    OperationTypeDTO,
    RBACElementTypeDTO,
    RoleSourceDTO,
    RoleStatusDTO,
)

__all__ = (
    "AssociationScopesEntitiesNode",
    "BulkAssignRoleFailureInfo",
    "BulkAssignRoleResultPayload",
    "BulkRevokeRoleFailureInfo",
    "BulkRevokeRoleResultPayload",
    "CreateRolePayload",
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "EntityNode",
    "PermissionNode",
    "PurgeRolePayload",
    "RoleAssignmentNode",
    "RoleNode",
    "ScopeEntityCombinationInfo",
    "UpdateRolePayload",
)


class RoleNode(BaseResponseModel):
    """Node model representing a role entity."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")
    source: RoleSourceDTO = Field(description="Role source")
    status: RoleStatusDTO = Field(description="Role status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    deleted_at: datetime | None = Field(default=None, description="Deletion timestamp")


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


class PermissionNode(BaseResponseModel):
    """Node representing a scoped RBAC permission."""

    id: UUID = Field(description="Permission ID")
    role_id: UUID = Field(description="Role this permission belongs to")
    scope_type: RBACElementTypeDTO = Field(description="Scope element type")
    scope_id: str = Field(description="Scope element ID")
    entity_type: RBACElementTypeDTO = Field(description="Entity element type")
    operation: OperationTypeDTO = Field(description="Operation type")


class EntityNode(BaseResponseModel):
    """Node representing an entity reference in the RBAC system."""

    entity_type: str = Field(description="Entity type value (e.g. 'user', 'project')")
    entity_id: str = Field(description="Entity identifier")


class AssociationScopesEntitiesNode(BaseResponseModel):
    """Node representing an association between a scope and an entity."""

    id: UUID = Field(description="Association ID")
    scope_type: str = Field(description="Scope element type value")
    scope_id: str = Field(description="Scope element ID")
    entity_type: str = Field(description="Entity element type value")
    entity_id: str = Field(description="Entity identifier")
    relation_type: str = Field(description="Relation type value")
    registered_at: datetime = Field(description="Registration timestamp")


class ScopeEntityCombinationInfo(BaseResponseModel):
    """Valid scope-entity type combination for RBAC permissions."""

    scope_type: RBACElementTypeDTO = Field(description="Scope element type")
    valid_entity_types: list[RBACElementTypeDTO] = Field(
        description="Valid entity types for this scope type"
    )

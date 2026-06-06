"""
Request DTOs for RBAC DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter

from .types import (
    OperationTypeFilter,
    OrderDirection,
    RBACElementTypeFilter,
    RoleSource,
    RoleSourceFilter,
    RoleStatus,
    RoleStatusFilter,
    ScopeInputDTO,
)

__all__ = (
    "AdminSearchEntitiesGQLInput",
    "AdminSearchPermissionsGQLInput",
    "SearchRoleAssignmentsInput",
    "SearchRolesInput",
    "AssignRoleInput",
    "BulkAddRolePermissionsInput",
    "BulkAssignRoleInput",
    "BulkRemoveRolePermissionsInput",
    "BulkRevokeRoleInput",
    "CreatePermissionInput",
    "CreateRoleInput",
    "DeletePermissionInput",
    "DeleteRoleInput",
    "EntityFilter",
    "EntityOrderBy",
    "PermissionFilter",
    "PermissionNestedFilter",
    "PermissionOrderBy",
    "PurgeRoleInput",
    "ReplaceRolePermissionsInput",
    "RevokeRoleInput",
    "RoleAssignmentFilter",
    "RoleAssignmentOrderBy",
    "RoleFilter",
    "RoleNestedFilter",
    "RoleOrderBy",
    "UpdatePermissionInput",
    "UpdateRoleInput",
    "UserNestedFilter",
)


class CreateRoleInput(BaseRequestModel):
    """Input for creating a role."""

    name: str = Field(min_length=1, max_length=256, description="Role name")
    description: str | None = Field(default=None, description="Role description")
    source: RoleSource = Field(default=RoleSource.CUSTOM, description="Role source")
    auto_assign: bool = Field(
        default=False,
        description=(
            "When true, the role is automatically granted to a user when the user is added "
            "to a scope this role is registered in."
        ),
    )
    scopes: list[ScopeInputDTO] | None = Field(
        default=None, description="Scopes to register the role in"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateRoleInput(BaseRequestModel):
    """Input for updating a role."""

    name: str | None = Field(default=None, description="Updated role name")
    description: str | Sentinel | None = Field(
        default=SENTINEL, description="Updated role description. Use SENTINEL to clear."
    )
    status: RoleStatus | None = Field(default=None, description="Updated role status")
    auto_assign: bool | None = Field(
        default=None,
        description=(
            "Updated value for the `auto_assign` flag. When true, the role is automatically "
            "granted to a user when the user is added to a scope this role is registered in."
        ),
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteRoleInput(BaseRequestModel):
    """Input for soft-deleting a role."""

    id: UUID = Field(description="Role ID to delete")


class PurgeRoleInput(BaseRequestModel):
    """Input for purging a role."""

    id: UUID = Field(description="Role ID to purge")


class CreatePermissionInput(BaseRequestModel):
    """Input for creating a scoped permission."""

    role_id: UUID = Field(description="Role ID to assign this permission to")
    scope_type: str = Field(description="Scope element type (e.g. 'domain', 'project')")
    scope_id: str = Field(description="Scope element ID")
    entity_type: str = Field(description="Entity element type (e.g. 'session', 'vfolder')")
    operation: str = Field(description="Operation type (e.g. 'read', 'create')")


class UpdatePermissionInput(BaseRequestModel):
    """Input for updating a scoped permission."""

    id: UUID = Field(description="Permission ID to update")
    scope_type: str | None = Field(default=None, description="Updated scope element type")
    scope_id: str | None = Field(default=None, description="Updated scope element ID")
    entity_type: str | None = Field(default=None, description="Updated entity element type")
    operation: str | None = Field(default=None, description="Updated operation type")


class DeletePermissionInput(BaseRequestModel):
    """Input for deleting a scoped permission."""

    id: UUID = Field(description="Permission ID to delete")


class AssignRoleInput(BaseRequestModel):
    """Input for assigning a role to a user."""

    user_id: UUID = Field(description="User ID to assign the role to")
    role_id: UUID = Field(description="Role ID to assign")
    project_id: UUID | None = Field(
        default=None,
        description="When provided, also add the user to this project",
    )


class RevokeRoleInput(BaseRequestModel):
    """Input for revoking a role from a user."""

    user_id: UUID = Field(description="User ID to revoke the role from")
    role_id: UUID = Field(description="Role ID to revoke")


class BulkAssignRoleInput(BaseRequestModel):
    """Input for bulk assigning a role to multiple users."""

    role_id: UUID = Field(description="Role ID to assign")
    user_ids: list[UUID] = Field(description="List of user IDs to assign the role to")
    project_id: UUID | None = Field(
        default=None,
        description="When provided, also add the users to this project",
    )


class BulkRevokeRoleInput(BaseRequestModel):
    """Input for bulk revoking a role from multiple users."""

    role_id: UUID = Field(description="Role ID to revoke")
    user_ids: list[UUID] = Field(description="List of user IDs to revoke the role from")


class BulkAddRolePermissionsInput(BaseRequestModel):
    """Input for bulk-adding scoped permissions across one or more roles."""

    permissions: list[CreatePermissionInput] = Field(
        description="Permission entries to insert. Duplicates are surfaced as failures.",
    )


class BulkRemoveRolePermissionsInput(BaseRequestModel):
    """Input for bulk-deleting permission rows by primary key.

    The permission row ID is globally unique, so a single call can remove rows
    belonging to multiple roles.
    """

    permission_ids: list[UUID] = Field(
        description="Permission row IDs to delete. Unknown IDs are silently ignored.",
    )


class ReplaceRolePermissionsInput(BaseRequestModel):
    """Input for replacing one role's entire scoped-permission set in one call.

    Every entry in ``permissions`` must carry the same ``role_id`` as the
    top-level field; the server rejects the call otherwise so the operation
    cannot accidentally span multiple roles.
    """

    role_id: UUID = Field(description="Role whose permission set is being replaced")
    permissions: list[CreatePermissionInput] = Field(
        description="New permission set for the role. An empty list clears all permissions.",
    )


class UserNestedFilter(BaseRequestModel):
    """Filter roles by their user assignments."""

    user_id: UUIDFilter | None = None
    AND: list[UserNestedFilter] | None = None
    OR: list[UserNestedFilter] | None = None
    NOT: list[UserNestedFilter] | None = None


UserNestedFilter.model_rebuild()


class RoleFilter(BaseRequestModel):
    """Filter for roles."""

    name: StringFilter | None = None
    source: RoleSourceFilter | None = None
    status: RoleStatusFilter | None = None
    assigned_user: UserNestedFilter | None = None
    AND: list[RoleFilter] | None = None
    OR: list[RoleFilter] | None = None
    NOT: list[RoleFilter] | None = None


RoleFilter.model_rebuild()


class RoleNestedFilter(BaseRequestModel):
    """Nested filter for roles within a role assignment."""

    name: StringFilter | None = None
    source: RoleSourceFilter | None = None
    status: RoleStatusFilter | None = None
    AND: list[RoleNestedFilter] | None = None
    OR: list[RoleNestedFilter] | None = None
    NOT: list[RoleNestedFilter] | None = None


RoleNestedFilter.model_rebuild()


class PermissionNestedFilter(BaseRequestModel):
    """Nested filter for permissions within a role assignment."""

    scope_id: StringFilter | None = None
    scope_type: RBACElementTypeFilter | None = None
    entity_type: RBACElementTypeFilter | None = None
    operation: OperationTypeFilter | None = None
    AND: list[PermissionNestedFilter] | None = None
    OR: list[PermissionNestedFilter] | None = None
    NOT: list[PermissionNestedFilter] | None = None


PermissionNestedFilter.model_rebuild()


class RoleAssignmentFilter(BaseRequestModel):
    """Filter for role assignments."""

    role_id: UUIDFilter | None = None
    role: RoleNestedFilter | None = None
    permission: PermissionNestedFilter | None = None
    username: StringFilter | None = None
    email: StringFilter | None = None
    AND: list[RoleAssignmentFilter] | None = None
    OR: list[RoleAssignmentFilter] | None = None
    NOT: list[RoleAssignmentFilter] | None = None


RoleAssignmentFilter.model_rebuild()


class EntityFilter(BaseRequestModel):
    """Filter for entity associations."""

    entity_type: RBACElementTypeFilter | None = None
    entity_id: StringFilter | None = None
    AND: list[EntityFilter] | None = None
    OR: list[EntityFilter] | None = None
    NOT: list[EntityFilter] | None = None


EntityFilter.model_rebuild()


class PermissionFilter(BaseRequestModel):
    """Filter for scoped permissions."""

    role_id: UUIDFilter | None = None
    scope_type: RBACElementTypeFilter | None = None
    scope_id: StringFilter | None = None
    entity_type: RBACElementTypeFilter | None = None
    created_at: DateTimeFilter | None = None
    AND: list[PermissionFilter] | None = None
    OR: list[PermissionFilter] | None = None
    NOT: list[PermissionFilter] | None = None


PermissionFilter.model_rebuild()


class RoleOrderBy(BaseRequestModel):
    """Order by specification for roles."""

    field: str
    direction: OrderDirection = OrderDirection.DESC


class RoleAssignmentOrderBy(BaseRequestModel):
    """Order by specification for role assignments."""

    field: str
    direction: OrderDirection = OrderDirection.DESC


class EntityOrderBy(BaseRequestModel):
    """Order by specification for entity associations."""

    field: str
    direction: OrderDirection = OrderDirection.DESC


class PermissionOrderBy(BaseRequestModel):
    """Order by specification for permissions."""

    field: str
    direction: OrderDirection = OrderDirection.DESC


class AdminSearchPermissionsGQLInput(BaseRequestModel):
    """GQL pagination search input for scoped permissions."""

    filter: PermissionFilter | None = None
    order: list[PermissionOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None


class SearchRolesInput(BaseRequestModel):
    """Pagination search input for roles."""

    filter: RoleFilter | None = None
    order: list[RoleOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None


class SearchRoleAssignmentsInput(BaseRequestModel):
    """Pagination search input for role assignments."""

    filter: RoleAssignmentFilter | None = None
    order: list[RoleAssignmentOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None


class AdminSearchEntitiesGQLInput(BaseRequestModel):
    """GQL pagination search input for entity associations."""

    filter: EntityFilter | None = None
    order: list[EntityOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None

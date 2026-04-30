"""V2 SDK client for the RBAC domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchEntitiesGQLInput,
    AdminSearchPermissionsGQLInput,
    AssignRoleInput,
    BulkAddRolePermissionsInput,
    BulkAssignRoleInput,
    BulkRemoveRolePermissionsInput,
    BulkRevokeRoleInput,
    CreatePermissionInput,
    CreateRoleInput,
    DeletePermissionInput,
    DeleteRoleInput,
    PurgeRoleInput,
    ReplaceRolePermissionsInput,
    RevokeRoleInput,
    SearchRoleAssignmentsInput,
    SearchRolesInput,
    UpdatePermissionInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    AdminSearchAssociationsPayload,
    AdminSearchPermissionsPayload,
    AdminSearchRolesPayload,
    BulkAddRolePermissionsPayload,
    BulkAssignRoleResultPayload,
    BulkRemoveRolePermissionsPayload,
    BulkRevokeRoleResultPayload,
    CreateRolePayload,
    DeletePermissionPayload,
    DeleteRolePayload,
    PermissionNode,
    PurgeRolePayload,
    ReplaceRolePermissionsPayload,
    RoleAssignmentNode,
    RoleNode,
    SearchRoleAssignmentsPayload,
    UpdateRolePayload,
)

_PATH = "/v2/rbac"


class V2RBACClient(BaseDomainClient):
    """SDK client for RBAC management."""

    # ------------------------------------------------------------------ Roles

    async def create_role(self, request: CreateRoleInput) -> CreateRolePayload:
        """Create a new role."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles",
            request=request,
            response_model=CreateRolePayload,
        )

    async def search_roles(self, request: SearchRolesInput) -> AdminSearchRolesPayload:
        """Search roles with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/search",
            request=request,
            response_model=AdminSearchRolesPayload,
        )

    async def project_search_roles(
        self, project_id: UUID, request: SearchRolesInput
    ) -> AdminSearchRolesPayload:
        """Search roles registered in a project scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/projects/{project_id}/search",
            request=request,
            response_model=AdminSearchRolesPayload,
        )

    async def get_role(self, role_id: UUID) -> RoleNode:
        """Retrieve a single role by UUID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/roles/{role_id}",
            response_model=RoleNode,
        )

    async def update_role(self, role_id: UUID, request: UpdateRoleInput) -> UpdateRolePayload:
        """Update an existing role."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/roles/{role_id}",
            request=request,
            response_model=UpdateRolePayload,
        )

    async def delete_role(self, request: DeleteRoleInput) -> DeleteRolePayload:
        """Soft-delete a role (marks status as DELETED)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/delete",
            request=request,
            response_model=DeleteRolePayload,
        )

    async def purge_role(self, request: PurgeRoleInput) -> PurgeRolePayload:
        """Hard-delete a role from the database."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/purge",
            request=request,
            response_model=PurgeRolePayload,
        )

    # ------------------------------------------------------------------ Permissions

    async def create_permission(self, request: CreatePermissionInput) -> PermissionNode:
        """Create a new scoped permission."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions",
            request=request,
            response_model=PermissionNode,
        )

    async def search_permissions(
        self, request: AdminSearchPermissionsGQLInput
    ) -> AdminSearchPermissionsPayload:
        """Search scoped permissions with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/search",
            request=request,
            response_model=AdminSearchPermissionsPayload,
        )

    async def update_permission(self, request: UpdatePermissionInput) -> PermissionNode:
        """Update an existing scoped permission."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/permissions",
            request=request,
            response_model=PermissionNode,
        )

    async def delete_permission(self, request: DeletePermissionInput) -> DeletePermissionPayload:
        """Hard-delete a scoped permission."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/delete",
            request=request,
            response_model=DeletePermissionPayload,
        )

    # -------------------------------------------------------- Bulk role permissions

    async def bulk_add_role_permissions(
        self,
        request: BulkAddRolePermissionsInput,
    ) -> BulkAddRolePermissionsPayload:
        """Bulk-insert scoped permission rows. Each entry carries its own role_id."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/bulk-add",
            request=request,
            response_model=BulkAddRolePermissionsPayload,
        )

    async def bulk_remove_role_permissions(
        self,
        request: BulkRemoveRolePermissionsInput,
    ) -> BulkRemoveRolePermissionsPayload:
        """Bulk-delete permission rows by primary key (cross-role allowed)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/bulk-remove",
            request=request,
            response_model=BulkRemoveRolePermissionsPayload,
        )

    async def replace_role_permissions(
        self,
        request: ReplaceRolePermissionsInput,
    ) -> ReplaceRolePermissionsPayload:
        """Replace one role's entire scoped-permission set in a single call."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/replace",
            request=request,
            response_model=ReplaceRolePermissionsPayload,
        )

    # ------------------------------------------------------------------ Assignments

    async def assign_role(self, request: AssignRoleInput) -> RoleAssignmentNode:
        """Assign a role to a user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments",
            request=request,
            response_model=RoleAssignmentNode,
        )

    async def revoke_role(self, request: RevokeRoleInput) -> RoleAssignmentNode:
        """Revoke a role from a user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/revoke",
            request=request,
            response_model=RoleAssignmentNode,
        )

    async def search_assignments(
        self, request: SearchRoleAssignmentsInput
    ) -> SearchRoleAssignmentsPayload:
        """Search role assignments with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/search",
            request=request,
            response_model=SearchRoleAssignmentsPayload,
        )

    async def my_search_assignments(
        self, request: SearchRoleAssignmentsInput
    ) -> SearchRoleAssignmentsPayload:
        """Search role assignments for the current authenticated user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/my/search",
            request=request,
            response_model=SearchRoleAssignmentsPayload,
        )

    async def bulk_assign_role(self, request: BulkAssignRoleInput) -> BulkAssignRoleResultPayload:
        """Bulk-assign a role to multiple users."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/bulk-assign",
            request=request,
            response_model=BulkAssignRoleResultPayload,
        )

    async def bulk_revoke_role(self, request: BulkRevokeRoleInput) -> BulkRevokeRoleResultPayload:
        """Bulk-revoke a role from multiple users."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/bulk-revoke",
            request=request,
            response_model=BulkRevokeRoleResultPayload,
        )

    # ------------------------------------------------------------------ Entities

    async def search_entities(
        self, request: AdminSearchEntitiesGQLInput
    ) -> AdminSearchAssociationsPayload:
        """Search entity associations with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/entities/search",
            request=request,
            response_model=AdminSearchAssociationsPayload,
        )

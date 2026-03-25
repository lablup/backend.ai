"""V2 SDK client for the RBAC domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchEntitiesGQLInput,
    AdminSearchPermissionsGQLInput,
    AdminSearchRoleAssignmentsGQLInput,
    AdminSearchRolesGQLInput,
    AssignRoleInput,
    BulkAssignRoleInput,
    BulkRevokeRoleInput,
    CreatePermissionInput,
    CreateRoleInput,
    DeletePermissionInput,
    DeleteRoleInput,
    PurgeRoleInput,
    RevokeRoleInput,
    UpdatePermissionInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    AdminSearchAssociationsPayload,
    AdminSearchPermissionsPayload,
    AdminSearchRoleAssignmentsPayload,
    AdminSearchRolesPayload,
    BulkAssignRoleResultPayload,
    BulkRevokeRoleResultPayload,
    CreateRolePayload,
    DeletePermissionPayload,
    DeleteRolePayload,
    PermissionNode,
    PurgeRolePayload,
    RoleAssignmentNode,
    RoleNode,
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

    async def search_roles(self, request: AdminSearchRolesGQLInput) -> AdminSearchRolesPayload:
        """Search roles with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/search",
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
        self, request: AdminSearchRoleAssignmentsGQLInput
    ) -> AdminSearchRoleAssignmentsPayload:
        """Search role assignments with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/assignments/search",
            request=request,
            response_model=AdminSearchRoleAssignmentsPayload,
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

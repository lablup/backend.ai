"""REST v2 handler for the RBAC domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import RoleIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.rbac import RBACAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2RBACHandler:
    """REST v2 handler for RBAC operations."""

    def __init__(self, *, adapter: RBACAdapter) -> None:
        self._adapter = adapter

    # ------------------------------------------------------------------ Roles

    async def create_role(
        self,
        body: BodyParam[CreateRoleInput],
    ) -> APIResponse:
        """Create a new role."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search_roles(
        self,
        body: BodyParam[AdminSearchRolesGQLInput],
    ) -> APIResponse:
        """Search roles with filters, orders, and pagination."""
        result = await self._adapter.admin_search_roles_gql(body.parsed)
        payload = AdminSearchRolesPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def get_role(
        self,
        path: PathParam[RoleIdPathParam],
    ) -> APIResponse:
        """Retrieve a single role by UUID."""
        result = await self._adapter.get(path.parsed.role_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_role(
        self,
        path: PathParam[RoleIdPathParam],
        body: BodyParam[UpdateRoleInput],
    ) -> APIResponse:
        """Update an existing role."""
        result = await self._adapter.update(path.parsed.role_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_role(
        self,
        body: BodyParam[DeleteRoleInput],
    ) -> APIResponse:
        """Soft-delete a role (marks status as DELETED)."""
        result = await self._adapter.delete(body.parsed.id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_role(
        self,
        body: BodyParam[PurgeRoleInput],
    ) -> APIResponse:
        """Hard-delete a role from the database."""
        result = await self._adapter.purge(body.parsed.id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ Permissions

    async def create_permission(
        self,
        body: BodyParam[CreatePermissionInput],
    ) -> APIResponse:
        """Create a new scoped permission."""
        result = await self._adapter.create_permission(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search_permissions(
        self,
        body: BodyParam[AdminSearchPermissionsGQLInput],
    ) -> APIResponse:
        """Search scoped permissions with filters, orders, and pagination."""
        result = await self._adapter.admin_search_permissions_gql(body.parsed)
        payload = AdminSearchPermissionsPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def update_permission(
        self,
        body: BodyParam[UpdatePermissionInput],
    ) -> APIResponse:
        """Update an existing scoped permission."""
        result = await self._adapter.update_permission(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_permission(
        self,
        body: BodyParam[DeletePermissionInput],
    ) -> APIResponse:
        """Hard-delete a scoped permission."""
        result = await self._adapter.delete_permission(body.parsed.id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ Assignments

    async def assign_role(
        self,
        body: BodyParam[AssignRoleInput],
    ) -> APIResponse:
        """Assign a role to a user."""
        result = await self._adapter.assign_role(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def revoke_role(
        self,
        body: BodyParam[RevokeRoleInput],
    ) -> APIResponse:
        """Revoke a role from a user."""
        result = await self._adapter.revoke_role(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_assignments(
        self,
        body: BodyParam[AdminSearchRoleAssignmentsGQLInput],
    ) -> APIResponse:
        """Search role assignments with filters, orders, and pagination."""
        result = await self._adapter.admin_search_role_assignments_gql(body.parsed)
        payload = AdminSearchRoleAssignmentsPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def bulk_assign_role(
        self,
        body: BodyParam[BulkAssignRoleInput],
    ) -> APIResponse:
        """Bulk-assign a role to multiple users."""
        result = await self._adapter.bulk_assign_role(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_revoke_role(
        self,
        body: BodyParam[BulkRevokeRoleInput],
    ) -> APIResponse:
        """Bulk-revoke a role from multiple users."""
        result = await self._adapter.bulk_revoke_role(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ Entities

    async def search_entities(
        self,
        body: BodyParam[AdminSearchEntitiesGQLInput],
    ) -> APIResponse:
        """Search entity associations with filters, orders, and pagination."""
        result = await self._adapter.admin_search_entities_gql(body.parsed)
        payload = AdminSearchAssociationsPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

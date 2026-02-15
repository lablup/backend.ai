from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.rbac.request import (
    AssignRoleRequest,
    CreateRoleRequest,
    DeleteRoleRequest,
    PurgeRoleRequest,
    RevokeRoleRequest,
    SearchEntitiesRequest,
    SearchRolesRequest,
    SearchScopesRequest,
    SearchUsersAssignedToRoleRequest,
    UpdateRoleRequest,
)
from ai.backend.common.dto.manager.rbac.response import (
    AssignRoleResponse,
    CreateRoleResponse,
    DeleteRoleResponse,
    GetEntityTypesResponse,
    GetRoleResponse,
    GetScopeTypesResponse,
    RevokeRoleResponse,
    SearchEntitiesResponse,
    SearchRolesResponse,
    SearchScopesResponse,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleResponse,
)


class RBACClient(BaseDomainClient):
    # ---- Role Management ----

    async def create_role(self, request: CreateRoleRequest) -> CreateRoleResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles",
            request=request,
            response_model=CreateRoleResponse,
        )

    async def search_roles(self, request: SearchRolesRequest) -> SearchRolesResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles/search",
            request=request,
            response_model=SearchRolesResponse,
        )

    async def get_role(self, role_id: UUID) -> GetRoleResponse:
        return await self._client.typed_request(
            "GET",
            f"/admin/rbac/roles/{role_id}",
            response_model=GetRoleResponse,
        )

    async def update_role(self, role_id: UUID, request: UpdateRoleRequest) -> UpdateRoleResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/admin/rbac/roles/{role_id}",
            request=request,
            response_model=UpdateRoleResponse,
        )

    async def delete_role(self, request: DeleteRoleRequest) -> DeleteRoleResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles/delete",
            request=request,
            response_model=DeleteRoleResponse,
        )

    async def purge_role(self, request: PurgeRoleRequest) -> DeleteRoleResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles/purge",
            request=request,
            response_model=DeleteRoleResponse,
        )

    # ---- Role Assignment ----

    async def assign_role(self, request: AssignRoleRequest) -> AssignRoleResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles/assign",
            request=request,
            response_model=AssignRoleResponse,
        )

    async def revoke_role(self, request: RevokeRoleRequest) -> RevokeRoleResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/rbac/roles/revoke",
            request=request,
            response_model=RevokeRoleResponse,
        )

    async def search_assigned_users(
        self, role_id: UUID, request: SearchUsersAssignedToRoleRequest
    ) -> SearchUsersAssignedToRoleResponse:
        return await self._client.typed_request(
            "POST",
            f"/admin/rbac/roles/{role_id}/assigned-users/search",
            request=request,
            response_model=SearchUsersAssignedToRoleResponse,
        )

    # ---- Scope Management ----

    async def get_scope_types(self) -> GetScopeTypesResponse:
        return await self._client.typed_request(
            "GET",
            "/admin/rbac/scope-types",
            response_model=GetScopeTypesResponse,
        )

    async def search_scopes(
        self, scope_type: str, request: SearchScopesRequest
    ) -> SearchScopesResponse:
        return await self._client.typed_request(
            "POST",
            f"/admin/rbac/scopes/{scope_type}/search",
            request=request,
            response_model=SearchScopesResponse,
        )

    # ---- Entity Management ----

    async def get_entity_types(self) -> GetEntityTypesResponse:
        return await self._client.typed_request(
            "GET",
            "/admin/rbac/entity-types",
            response_model=GetEntityTypesResponse,
        )

    async def search_entities(
        self,
        scope_type: str,
        scope_id: str,
        entity_type: str,
        request: SearchEntitiesRequest,
    ) -> SearchEntitiesResponse:
        return await self._client.typed_request(
            "POST",
            f"/admin/rbac/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search",
            request=request,
            response_model=SearchEntitiesResponse,
        )

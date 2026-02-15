from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.group import (
    AddGroupMembersRequest,
    AddGroupMembersResponse,
    CreateGroupRequest,
    CreateGroupResponse,
    DeleteGroupResponse,
    GetGroupResponse,
    ListGroupMembersRequest,
    ListGroupMembersResponse,
    RemoveGroupMembersRequest,
    RemoveGroupMembersResponse,
    SearchGroupsRequest,
    SearchGroupsResponse,
    UpdateGroupRequest,
    UpdateGroupResponse,
)
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse

_BASE_PATH = "/group"
_GROUPS_PATH = "/groups"


class GroupClient(BaseDomainClient):
    # ---------------------------------------------------------------------------
    # Registry Quota (existing)
    # ---------------------------------------------------------------------------

    async def create_registry_quota(
        self,
        request: CreateRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )

    async def read_registry_quota(
        self,
        request: ReadRegistryQuotaReq,
    ) -> RegistryQuotaResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/registry-quota",
            response_model=RegistryQuotaResponse,
            params=params,
        )

    async def update_registry_quota(
        self,
        request: UpdateRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "PATCH",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )

    async def delete_registry_quota(
        self,
        request: DeleteRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "DELETE",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )

    # ---------------------------------------------------------------------------
    # Group CRUD
    # ---------------------------------------------------------------------------

    async def create(
        self,
        request: CreateGroupRequest,
    ) -> CreateGroupResponse:
        return await self._client.typed_request(
            "POST",
            _GROUPS_PATH,
            request=request,
            response_model=CreateGroupResponse,
        )

    async def search(
        self,
        request: SearchGroupsRequest,
    ) -> SearchGroupsResponse:
        return await self._client.typed_request(
            "POST",
            f"{_GROUPS_PATH}/search",
            request=request,
            response_model=SearchGroupsResponse,
        )

    async def get(
        self,
        group_id: uuid.UUID,
    ) -> GetGroupResponse:
        return await self._client.typed_request(
            "GET",
            f"{_GROUPS_PATH}/{group_id}",
            response_model=GetGroupResponse,
        )

    async def update(
        self,
        group_id: uuid.UUID,
        request: UpdateGroupRequest,
    ) -> UpdateGroupResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{_GROUPS_PATH}/{group_id}",
            request=request,
            response_model=UpdateGroupResponse,
        )

    async def delete(
        self,
        group_id: uuid.UUID,
    ) -> DeleteGroupResponse:
        return await self._client.typed_request(
            "DELETE",
            f"{_GROUPS_PATH}/{group_id}",
            response_model=DeleteGroupResponse,
        )

    # ---------------------------------------------------------------------------
    # Member Management
    # ---------------------------------------------------------------------------

    async def add_members(
        self,
        group_id: uuid.UUID,
        request: AddGroupMembersRequest,
    ) -> AddGroupMembersResponse:
        return await self._client.typed_request(
            "POST",
            f"{_GROUPS_PATH}/{group_id}/members",
            request=request,
            response_model=AddGroupMembersResponse,
        )

    async def remove_members(
        self,
        group_id: uuid.UUID,
        request: RemoveGroupMembersRequest,
    ) -> RemoveGroupMembersResponse:
        return await self._client.typed_request(
            "DELETE",
            f"{_GROUPS_PATH}/{group_id}/members",
            request=request,
            response_model=RemoveGroupMembersResponse,
        )

    async def list_members(
        self,
        group_id: uuid.UUID,
        request: ListGroupMembersRequest,
    ) -> ListGroupMembersResponse:
        return await self._client.typed_request(
            "POST",
            f"{_GROUPS_PATH}/{group_id}/members/search",
            request=request,
            response_model=ListGroupMembersResponse,
        )

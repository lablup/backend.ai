from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.group import GroupClient
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
from ai.backend.common.dto.manager.group.request import GroupFilter
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _no_content_response() -> AsyncMock:
    resp = AsyncMock()
    resp.status = 204
    return resp


def _make_group_client(mock_session: MagicMock) -> GroupClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return GroupClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

_SAMPLE_GROUP_ID = uuid4()
_SAMPLE_USER_ID_1 = uuid4()
_SAMPLE_USER_ID_2 = uuid4()

_SAMPLE_GROUP_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_GROUP_ID),
    "name": "test-group",
    "description": "A test group",
    "is_active": True,
    "created_at": "2025-01-01T00:00:00",
    "modified_at": "2025-01-01T00:00:00",
    "domain_name": "default",
    "integration_id": None,
    "total_resource_slots": None,
    "allowed_vfolder_hosts": None,
    "resource_policy": None,
    "container_registry": None,
}

_SAMPLE_MEMBER_DTO_1: dict[str, Any] = {
    "user_id": str(_SAMPLE_USER_ID_1),
    "group_id": str(_SAMPLE_GROUP_ID),
}

_SAMPLE_MEMBER_DTO_2: dict[str, Any] = {
    "user_id": str(_SAMPLE_USER_ID_2),
    "group_id": str(_SAMPLE_GROUP_ID),
}


# ---------------------------------------------------------------------------
# Registry Quota (existing tests, unchanged)
# ---------------------------------------------------------------------------


class TestCreateRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_post_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = CreateRegistryQuotaReq(group_id="grp-001", quota=100)
        await gc.create_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"
        assert body["quota"] == 100


class TestReadRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_get_with_params(self) -> None:
        resp = _json_response({"result": 100})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = ReadRegistryQuotaReq(group_id="grp-001")
        result = await gc.read_registry_quota(request)

        assert isinstance(result, RegistryQuotaResponse)
        assert result.result == 100
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["params"]["group_id"] == "grp-001"


class TestUpdateRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_patch_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = UpdateRegistryQuotaReq(group_id="grp-001", quota=200)
        await gc.update_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"
        assert body["quota"] == 200


class TestDeleteRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_delete_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = DeleteRegistryQuotaReq(group_id="grp-001")
        await gc.delete_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "DELETE"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------


class TestGroupCRUD:
    @pytest.mark.asyncio
    async def test_create_group(self) -> None:
        resp = _json_response({"group": _SAMPLE_GROUP_DTO})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = CreateGroupRequest(
            name="test-group",
            domain_name="default",
            description="A test group",
        )
        result = await gc.create(request)

        assert isinstance(result, CreateGroupResponse)
        assert result.group.name == "test-group"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/groups")
        assert body is not None
        assert body["name"] == "test-group"
        assert body["domain_name"] == "default"

    @pytest.mark.asyncio
    async def test_search_groups(self) -> None:
        resp = _json_response({
            "groups": [_SAMPLE_GROUP_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        result = await gc.search(SearchGroupsRequest())

        assert isinstance(result, SearchGroupsResponse)
        assert len(result.groups) == 1
        assert result.pagination.total == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/groups/search")
        assert body is not None

    @pytest.mark.asyncio
    async def test_search_groups_with_filter(self) -> None:
        resp = _json_response({
            "groups": [_SAMPLE_GROUP_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = SearchGroupsRequest(
            filter=GroupFilter(
                name=StringFilter(contains="test"),
                is_active=True,
            ),
            limit=10,
            offset=0,
        )
        result = await gc.search(request)

        assert isinstance(result, SearchGroupsResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert body is not None
        assert body["filter"]["name"]["contains"] == "test"
        assert body["filter"]["is_active"] is True
        assert body["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_group(self) -> None:
        resp = _json_response({"group": _SAMPLE_GROUP_DTO})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        result = await gc.get(_SAMPLE_GROUP_ID)

        assert isinstance(result, GetGroupResponse)
        assert result.group.name == "test-group"
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert str(_SAMPLE_GROUP_ID) in url

    @pytest.mark.asyncio
    async def test_update_group(self) -> None:
        updated_dto = {**_SAMPLE_GROUP_DTO, "name": "updated-group"}
        resp = _json_response({"group": updated_dto})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        result = await gc.update(
            _SAMPLE_GROUP_ID,
            UpdateGroupRequest(name="updated-group"),
        )

        assert isinstance(result, UpdateGroupResponse)
        assert result.group.name == "updated-group"
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert str(_SAMPLE_GROUP_ID) in url
        assert body is not None
        assert body["name"] == "updated-group"

    @pytest.mark.asyncio
    async def test_delete_group(self) -> None:
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        result = await gc.delete(_SAMPLE_GROUP_ID)

        assert isinstance(result, DeleteGroupResponse)
        assert result.deleted is True
        method, url, _ = _last_request_call(mock_session)
        assert method == "DELETE"
        assert str(_SAMPLE_GROUP_ID) in url


# ---------------------------------------------------------------------------
# Member Management
# ---------------------------------------------------------------------------


class TestGroupMembers:
    @pytest.mark.asyncio
    async def test_add_members(self) -> None:
        resp = _json_response({"members": [_SAMPLE_MEMBER_DTO_1, _SAMPLE_MEMBER_DTO_2]})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = AddGroupMembersRequest(user_ids=[_SAMPLE_USER_ID_1, _SAMPLE_USER_ID_2])
        result = await gc.add_members(_SAMPLE_GROUP_ID, request)

        assert isinstance(result, AddGroupMembersResponse)
        assert len(result.members) == 2
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/groups/{_SAMPLE_GROUP_ID}/members" in url
        assert body is not None
        assert len(body["user_ids"]) == 2

    @pytest.mark.asyncio
    async def test_remove_members(self) -> None:
        resp = _json_response({"removed_count": 1})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = RemoveGroupMembersRequest(user_ids=[_SAMPLE_USER_ID_1])
        result = await gc.remove_members(_SAMPLE_GROUP_ID, request)

        assert isinstance(result, RemoveGroupMembersResponse)
        assert result.removed_count == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "DELETE"
        assert f"/groups/{_SAMPLE_GROUP_ID}/members" in url
        assert body is not None
        assert len(body["user_ids"]) == 1

    @pytest.mark.asyncio
    async def test_list_members(self) -> None:
        resp = _json_response({
            "members": [_SAMPLE_MEMBER_DTO_1, _SAMPLE_MEMBER_DTO_2],
            "pagination": {"total": 2, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = ListGroupMembersRequest()
        result = await gc.list_members(_SAMPLE_GROUP_ID, request)

        assert isinstance(result, ListGroupMembersResponse)
        assert len(result.members) == 2
        assert result.pagination.total == 2
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/groups/{_SAMPLE_GROUP_ID}/members/search" in url
        assert body is not None

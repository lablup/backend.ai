from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.user import UserClient
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    PurgeUserRequest,
    PurgeUserResponse,
    SearchUsersRequest,
    SearchUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserFilter,
    UserRole,
    UserStatus,
)

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


def _make_user_client(mock_session: MagicMock) -> UserClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return UserClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SAMPLE_USER_ID = uuid4()

_SAMPLE_USER_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_USER_ID),
    "username": "testuser",
    "email": "testuser@example.com",
    "need_password_change": False,
    "full_name": "Test User",
    "description": "A test user",
    "status": "active",
    "status_info": None,
    "created_at": "2025-01-01T00:00:00",
    "modified_at": "2025-01-01T00:00:00",
    "domain_name": "default",
    "role": "user",
    "resource_policy": "default",
    "allowed_client_ip": None,
    "totp_activated": False,
    "sudo_session_enabled": False,
    "main_access_key": None,
    "container_uid": None,
    "container_main_gid": None,
    "container_gids": None,
}


# ---------------------------------------------------------------------------
# User CRUD Tests
# ---------------------------------------------------------------------------


class TestUserCRUD:
    @pytest.mark.asyncio
    async def test_create_user(self) -> None:
        resp = _json_response({"user": _SAMPLE_USER_DTO})
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        request = CreateUserRequest(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
            domain_name="default",
        )
        result = await uc.create(request)

        assert isinstance(result, CreateUserResponse)
        assert result.user.email == "testuser@example.com"
        assert result.user.username == "testuser"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/users")
        assert body is not None
        assert body["email"] == "testuser@example.com"
        assert body["username"] == "testuser"
        assert body["domain_name"] == "default"

    @pytest.mark.asyncio
    async def test_get_user(self) -> None:
        resp = _json_response({"user": _SAMPLE_USER_DTO})
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        result = await uc.get(_SAMPLE_USER_ID)

        assert isinstance(result, GetUserResponse)
        assert result.user.username == "testuser"
        assert result.user.email == "testuser@example.com"
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert str(_SAMPLE_USER_ID) in url

    @pytest.mark.asyncio
    async def test_search_users(self) -> None:
        resp = _json_response({
            "items": [_SAMPLE_USER_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        result = await uc.search(SearchUsersRequest())

        assert isinstance(result, SearchUsersResponse)
        assert len(result.items) == 1
        assert result.pagination.total == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/users/search")
        assert body is not None

    @pytest.mark.asyncio
    async def test_search_users_with_filter(self) -> None:
        resp = _json_response({
            "items": [_SAMPLE_USER_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        request = SearchUsersRequest(
            filter=UserFilter(
                email=StringFilter(contains="test"),
                status=[UserStatus.ACTIVE],
                role=[UserRole.USER],
            ),
            limit=10,
            offset=0,
        )
        result = await uc.search(request)

        assert isinstance(result, SearchUsersResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert body is not None
        assert body["filter"]["email"]["contains"] == "test"
        assert body["filter"]["status"] == ["active"]
        assert body["filter"]["role"] == ["user"]
        assert body["limit"] == 10

    @pytest.mark.asyncio
    async def test_update_user(self) -> None:
        updated_dto = {**_SAMPLE_USER_DTO, "full_name": "Updated Name"}
        resp = _json_response({"user": updated_dto})
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        result = await uc.update(
            _SAMPLE_USER_ID,
            UpdateUserRequest(full_name="Updated Name"),
        )

        assert isinstance(result, UpdateUserResponse)
        assert result.user.full_name == "Updated Name"
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert str(_SAMPLE_USER_ID) in url
        assert body is not None
        assert body["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self) -> None:
        resp = _json_response({"success": True})
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        request = DeleteUserRequest(user_id=_SAMPLE_USER_ID)
        result = await uc.delete(request)

        assert isinstance(result, DeleteUserResponse)
        assert result.success is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/users/delete")
        assert body is not None
        assert body["user_id"] == _SAMPLE_USER_ID

    @pytest.mark.asyncio
    async def test_purge_user(self) -> None:
        resp = _json_response({"success": True})
        mock_session = _make_request_session(resp)
        uc = _make_user_client(mock_session)

        request = PurgeUserRequest(
            user_id=_SAMPLE_USER_ID,
            purge_shared_vfolders=True,
            delegate_endpoint_ownership=True,
        )
        result = await uc.purge(request)

        assert isinstance(result, PurgeUserResponse)
        assert result.success is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/users/purge")
        assert body is not None
        assert body["user_id"] == _SAMPLE_USER_ID
        assert body["purge_shared_vfolders"] is True
        assert body["delegate_endpoint_ownership"] is True

"""Unit tests for RBACClient (SDK v2)."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.rbac import RBACClient
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.rbac.request import (
    AssignRoleRequest,
    CreateRoleRequest,
    DeleteRoleRequest,
    PurgeRoleRequest,
    RevokeRoleRequest,
    RoleFilter,
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
from ai.backend.common.dto.manager.rbac.types import RoleSource, RoleStatus

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_SAMPLE_ROLE_ID = str(uuid.uuid4())
_SAMPLE_USER_ID = str(uuid.uuid4())
_NOW_ISO = "2025-01-01T00:00:00+00:00"


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock aiohttp session whose ``request()`` returns *resp*."""
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


def _make_rbac_client(mock_session: MagicMock) -> RBACClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return RBACClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


def _sample_role_dict(role_id: str = _SAMPLE_ROLE_ID) -> dict[str, Any]:
    return {
        "id": role_id,
        "name": "test-role",
        "source": RoleSource.CUSTOM.value,
        "status": RoleStatus.ACTIVE.value,
        "created_at": _NOW_ISO,
        "updated_at": _NOW_ISO,
        "deleted_at": None,
        "description": "A test role",
    }


class TestRoleCreate:
    async def test_create_role(self) -> None:
        resp = _json_response({"role": _sample_role_dict()})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.create_role(
            CreateRoleRequest(
                name="test-role",
                source=RoleSource.CUSTOM,
                status=RoleStatus.ACTIVE,
                description="A test role",
            )
        )

        assert isinstance(result, CreateRoleResponse)
        assert result.role.name == "test-role"
        assert result.role.source == RoleSource.CUSTOM
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles")
        assert body is not None
        assert body["name"] == "test-role"


class TestRoleSearch:
    async def test_search_roles(self) -> None:
        resp = _json_response({
            "roles": [_sample_role_dict()],
            "pagination": {"total": 1, "offset": 0, "limit": 100},
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.search_roles(SearchRolesRequest())

        assert isinstance(result, SearchRolesResponse)
        assert len(result.roles) == 1
        assert result.pagination.total == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles/search")

    async def test_search_roles_with_filter(self) -> None:
        resp = _json_response({
            "roles": [_sample_role_dict()],
            "pagination": {"total": 1, "offset": 0, "limit": 100},
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains="test")),
                limit=10,
                offset=0,
            )
        )

        assert isinstance(result, SearchRolesResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert body is not None
        assert body["filter"]["name"]["contains"] == "test"
        assert body["limit"] == 10


class TestRoleGet:
    async def test_get_role(self) -> None:
        role_id = uuid.uuid4()
        resp = _json_response({"role": _sample_role_dict(str(role_id))})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.get_role(role_id)

        assert isinstance(result, GetRoleResponse)
        assert result.role.id == role_id
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert url.endswith(f"/admin/rbac/roles/{role_id}")
        assert body is None


class TestRoleUpdate:
    async def test_update_role(self) -> None:
        role_id = uuid.uuid4()
        updated = _sample_role_dict(str(role_id))
        updated["name"] = "updated-role"
        resp = _json_response({"role": updated})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.update_role(role_id, UpdateRoleRequest(name="updated-role"))

        assert isinstance(result, UpdateRoleResponse)
        assert result.role.name == "updated-role"
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert url.endswith(f"/admin/rbac/roles/{role_id}")
        assert body is not None
        assert body["name"] == "updated-role"


class TestRoleDelete:
    async def test_delete_role(self) -> None:
        role_id = uuid.uuid4()
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.delete_role(DeleteRoleRequest(role_id=role_id))

        assert isinstance(result, DeleteRoleResponse)
        assert result.deleted is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles/delete")
        assert body is not None
        assert body["role_id"] == str(role_id)


class TestRolePurge:
    async def test_purge_role(self) -> None:
        role_id = uuid.uuid4()
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.purge_role(PurgeRoleRequest(role_id=role_id))

        assert isinstance(result, DeleteRoleResponse)
        assert result.deleted is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles/purge")
        assert body is not None
        assert body["role_id"] == str(role_id)


class TestRoleAssign:
    async def test_assign_role(self) -> None:
        role_id = uuid.uuid4()
        user_id = uuid.uuid4()
        resp = _json_response({
            "user_id": str(user_id),
            "role_id": str(role_id),
            "granted_by": None,
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.assign_role(AssignRoleRequest(user_id=user_id, role_id=role_id))

        assert isinstance(result, AssignRoleResponse)
        assert result.user_id == user_id
        assert result.role_id == role_id
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles/assign")
        assert body is not None
        assert body["user_id"] == str(user_id)
        assert body["role_id"] == str(role_id)


class TestRoleRevoke:
    async def test_revoke_role(self) -> None:
        role_id = uuid.uuid4()
        user_id = uuid.uuid4()
        resp = _json_response({
            "user_id": str(user_id),
            "role_id": str(role_id),
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.revoke_role(RevokeRoleRequest(user_id=user_id, role_id=role_id))

        assert isinstance(result, RevokeRoleResponse)
        assert result.user_id == user_id
        assert result.role_id == role_id
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/roles/revoke")
        assert body is not None


class TestSearchAssignedUsers:
    async def test_search_assigned_users(self) -> None:
        role_id = uuid.uuid4()
        user_id = uuid.uuid4()
        resp = _json_response({
            "users": [
                {
                    "user_id": str(user_id),
                    "granted_by": None,
                    "granted_at": _NOW_ISO,
                }
            ],
            "pagination": {"total": 1, "offset": 0, "limit": 100},
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.search_assigned_users(role_id, SearchUsersAssignedToRoleRequest())

        assert isinstance(result, SearchUsersAssignedToRoleResponse)
        assert len(result.users) == 1
        assert result.users[0].user_id == user_id
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith(f"/admin/rbac/roles/{role_id}/assigned-users/search")


class TestScopeTypes:
    async def test_get_scope_types(self) -> None:
        resp = _json_response({"items": ["domain", "project", "user"]})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.get_scope_types()

        assert isinstance(result, GetScopeTypesResponse)
        assert len(result.items) == 3
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert url.endswith("/admin/rbac/scope-types")
        assert body is None


class TestSearchScopes:
    async def test_search_scopes(self) -> None:
        resp = _json_response({
            "items": [
                {
                    "scope_type": "domain",
                    "scope_id": "default",
                    "name": "default",
                }
            ],
            "pagination": {"total": 1, "offset": 0, "limit": 100},
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.search_scopes("domain", SearchScopesRequest())

        assert isinstance(result, SearchScopesResponse)
        assert len(result.items) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/rbac/scopes/domain/search")


class TestEntityTypes:
    async def test_get_entity_types(self) -> None:
        resp = _json_response({"items": ["user", "project"]})
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        result = await rc.get_entity_types()

        assert isinstance(result, GetEntityTypesResponse)
        assert len(result.items) == 2
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert url.endswith("/admin/rbac/entity-types")
        assert body is None


class TestSearchEntities:
    async def test_search_entities(self) -> None:
        resp = _json_response({
            "items": [
                {"entity_type": "user", "entity_id": str(uuid.uuid4())},
            ],
            "pagination": {"total": 1, "offset": 0, "limit": 100},
        })
        mock_session = _make_request_session(resp)
        rc = _make_rbac_client(mock_session)

        scope_id = str(uuid.uuid4())
        result = await rc.search_entities("domain", scope_id, "user", SearchEntitiesRequest())

        assert isinstance(result, SearchEntitiesResponse)
        assert len(result.items) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith(f"/admin/rbac/scopes/domain/{scope_id}/entities/user/search")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.rbac import RBACClient
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
from ai.backend.common.dto.manager.rbac.types import RoleSource, RoleStatus

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_ROLE_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_GRANTED_BY = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

_ROLE_PAYLOAD = {
    "id": str(_ROLE_ID),
    "name": "admin",
    "source": "custom",
    "status": "active",
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
    "description": "Admin role",
}


def _make_client(
    mock_session: MagicMock | None = None,
    config: ClientConfig | None = None,
) -> BackendAIClient:
    return BackendAIClient(
        config or _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


class TestRBACClient:
    # ---- Role Management ----

    @pytest.mark.asyncio
    async def test_create_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(return_value={"role": _ROLE_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = CreateRoleRequest(
            name="admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            description="Admin role",
        )
        result = await rbac.create_role(request)

        assert isinstance(result, CreateRoleResponse)
        assert result.role.name == "admin"
        assert result.role.id == _ROLE_ID

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "admin"

    @pytest.mark.asyncio
    async def test_search_roles(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "roles": [_ROLE_PAYLOAD],
                "pagination": {"total": 1, "offset": 0, "limit": 20},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = SearchRolesRequest()
        result = await rbac.search_roles(request)

        assert isinstance(result, SearchRolesResponse)
        assert len(result.roles) == 1
        assert result.pagination.total == 1

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles/search" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_get_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"role": _ROLE_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        result = await rbac.get_role(_ROLE_ID)

        assert isinstance(result, GetRoleResponse)
        assert result.role.id == _ROLE_ID

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert f"/admin/rbac/roles/{_ROLE_ID}" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_update_role(self) -> None:
        updated = {**_ROLE_PAYLOAD, "name": "superadmin"}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"role": updated})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = UpdateRoleRequest(name="superadmin")
        result = await rbac.update_role(_ROLE_ID, request)

        assert isinstance(result, UpdateRoleResponse)
        assert result.role.name == "superadmin"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "PATCH"
        assert f"/admin/rbac/roles/{_ROLE_ID}" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "superadmin"

    @pytest.mark.asyncio
    async def test_delete_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"deleted": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = DeleteRoleRequest(role_id=_ROLE_ID)
        result = await rbac.delete_role(request)

        assert isinstance(result, DeleteRoleResponse)
        assert result.deleted is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles/delete" in str(call_args.args[1])
        assert str(call_args.kwargs["json"]["role_id"]) == str(_ROLE_ID)

    @pytest.mark.asyncio
    async def test_purge_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"deleted": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = PurgeRoleRequest(role_id=_ROLE_ID)
        result = await rbac.purge_role(request)

        assert isinstance(result, DeleteRoleResponse)
        assert result.deleted is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles/purge" in str(call_args.args[1])
        assert str(call_args.kwargs["json"]["role_id"]) == str(_ROLE_ID)

    # ---- Role Assignment ----

    @pytest.mark.asyncio
    async def test_assign_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(
            return_value={
                "user_id": str(_USER_ID),
                "role_id": str(_ROLE_ID),
                "granted_by": str(_GRANTED_BY),
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = AssignRoleRequest(user_id=_USER_ID, role_id=_ROLE_ID, granted_by=_GRANTED_BY)
        result = await rbac.assign_role(request)

        assert isinstance(result, AssignRoleResponse)
        assert result.user_id == _USER_ID
        assert result.role_id == _ROLE_ID

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles/assign" in str(call_args.args[1])
        assert str(call_args.kwargs["json"]["user_id"]) == str(_USER_ID)

    @pytest.mark.asyncio
    async def test_revoke_role(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "user_id": str(_USER_ID),
                "role_id": str(_ROLE_ID),
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = RevokeRoleRequest(user_id=_USER_ID, role_id=_ROLE_ID)
        result = await rbac.revoke_role(request)

        assert isinstance(result, RevokeRoleResponse)
        assert result.user_id == _USER_ID
        assert result.role_id == _ROLE_ID

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/roles/revoke" in str(call_args.args[1])
        assert str(call_args.kwargs["json"]["user_id"]) == str(_USER_ID)

    @pytest.mark.asyncio
    async def test_search_assigned_users(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "users": [
                    {
                        "user_id": str(_USER_ID),
                        "granted_by": str(_GRANTED_BY),
                        "granted_at": "2025-01-01T00:00:00+00:00",
                    }
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 20},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = SearchUsersAssignedToRoleRequest()
        result = await rbac.search_assigned_users(_ROLE_ID, request)

        assert isinstance(result, SearchUsersAssignedToRoleResponse)
        assert len(result.users) == 1
        assert result.users[0].user_id == _USER_ID

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert f"/admin/rbac/roles/{_ROLE_ID}/assigned-users/search" in str(call_args.args[1])

    # ---- Scope Management ----

    @pytest.mark.asyncio
    async def test_get_scope_types(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"items": ["domain", "project", "user"]})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        result = await rbac.get_scope_types()

        assert isinstance(result, GetScopeTypesResponse)
        assert len(result.items) == 3

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/rbac/scope-types" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search_scopes(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {"scope_type": "domain", "scope_id": "default", "name": "Default Domain"}
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 20},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = SearchScopesRequest()
        result = await rbac.search_scopes("domain", request)

        assert isinstance(result, SearchScopesResponse)
        assert len(result.items) == 1
        assert result.items[0].name == "Default Domain"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/scopes/domain/search" in str(call_args.args[1])

    # ---- Entity Management ----

    @pytest.mark.asyncio
    async def test_get_entity_types(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"items": ["session", "vfolder", "image"]})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        result = await rbac.get_entity_types()

        assert isinstance(result, GetEntityTypesResponse)
        assert len(result.items) == 3

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/rbac/entity-types" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search_entities(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [{"entity_type": "session", "entity_id": "sess-001"}],
                "pagination": {"total": 1, "offset": 0, "limit": 20},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rbac = RBACClient(client)

        request = SearchEntitiesRequest()
        result = await rbac.search_entities("domain", "default", "session", request)

        assert isinstance(result, SearchEntitiesResponse)
        assert len(result.items) == 1
        assert result.items[0].entity_id == "sess-001"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/rbac/scopes/domain/default/entities/session/search" in str(call_args.args[1])

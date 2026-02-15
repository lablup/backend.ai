from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.resource_policy import ResourcePolicyClient
from ai.backend.common.dto.manager.resource_policy.request import (
    CreateKeypairResourcePolicyRequest,
    CreateProjectResourcePolicyRequest,
    CreateUserResourcePolicyRequest,
    DeleteKeypairResourcePolicyRequest,
    DeleteProjectResourcePolicyRequest,
    DeleteUserResourcePolicyRequest,
    SearchKeypairResourcePoliciesRequest,
    SearchProjectResourcePoliciesRequest,
    SearchUserResourcePoliciesRequest,
    UpdateKeypairResourcePolicyRequest,
    UpdateProjectResourcePolicyRequest,
    UpdateUserResourcePolicyRequest,
)
from ai.backend.common.dto.manager.resource_policy.response import (
    CreateKeypairResourcePolicyResponse,
    CreateProjectResourcePolicyResponse,
    CreateUserResourcePolicyResponse,
    DeleteKeypairResourcePolicyResponse,
    DeleteProjectResourcePolicyResponse,
    DeleteUserResourcePolicyResponse,
    GetKeypairResourcePolicyResponse,
    GetProjectResourcePolicyResponse,
    GetUserResourcePolicyResponse,
    SearchKeypairResourcePoliciesResponse,
    SearchProjectResourcePoliciesResponse,
    SearchUserResourcePoliciesResponse,
    UpdateKeypairResourcePolicyResponse,
    UpdateProjectResourcePolicyResponse,
    UpdateUserResourcePolicyResponse,
)
from ai.backend.common.types import DefaultForUnspecified

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_KEYPAIR_POLICY_PAYLOAD = {
    "name": "default",
    "created_at": "2025-01-01T00:00:00+00:00",
    "default_for_unspecified": "LIMITED",
    "total_resource_slots": {"cpu": "4", "mem": "8g"},
    "max_session_lifetime": 0,
    "max_concurrent_sessions": 5,
    "max_pending_session_count": None,
    "max_pending_session_resource_slots": None,
    "max_concurrent_sftp_sessions": 2,
    "max_containers_per_session": 1,
    "idle_timeout": 1800,
    "allowed_vfolder_hosts": {"local": ["create-vfolder", "mount-in-session"]},
}

_USER_POLICY_PAYLOAD = {
    "name": "default-user",
    "created_at": "2025-01-01T00:00:00+00:00",
    "max_vfolder_count": 10,
    "max_quota_scope_size": 1073741824,
    "max_session_count_per_model_session": 3,
    "max_customized_image_count": 5,
}

_PROJECT_POLICY_PAYLOAD = {
    "name": "default-project",
    "created_at": "2025-01-01T00:00:00+00:00",
    "max_vfolder_count": 50,
    "max_quota_scope_size": 10737418240,
    "max_network_count": 10,
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


class TestKeypairResourcePolicy:
    @pytest.mark.asyncio
    async def test_create_keypair_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(return_value={"item": _KEYPAIR_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = CreateKeypairResourcePolicyRequest(
            name="default",
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots={"cpu": "4", "mem": "8g"},
            max_concurrent_sessions=5,
            idle_timeout=1800,
        )
        result = await rp.create_keypair_policy(request)

        assert isinstance(result, CreateKeypairResourcePolicyResponse)
        assert result.item.name == "default"
        assert result.item.default_for_unspecified == DefaultForUnspecified.LIMITED

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/keypair" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default"

    @pytest.mark.asyncio
    async def test_get_keypair_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": _KEYPAIR_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        result = await rp.get_keypair_policy("default")

        assert isinstance(result, GetKeypairResourcePolicyResponse)
        assert result.item.name == "default"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/resource-policies/keypair/default" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search_keypair_policies(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [_KEYPAIR_POLICY_PAYLOAD],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = SearchKeypairResourcePoliciesRequest()
        result = await rp.search_keypair_policies(request)

        assert isinstance(result, SearchKeypairResourcePoliciesResponse)
        assert len(result.items) == 1
        assert result.pagination.total == 1

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/keypair/search" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_update_keypair_policy(self) -> None:
        updated = {**_KEYPAIR_POLICY_PAYLOAD, "max_concurrent_sessions": 10}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": updated})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = UpdateKeypairResourcePolicyRequest(max_concurrent_sessions=10)
        result = await rp.update_keypair_policy("default", request)

        assert isinstance(result, UpdateKeypairResourcePolicyResponse)
        assert result.item.max_concurrent_sessions == 10

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "PATCH"
        assert "/admin/resource-policies/keypair/default" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_delete_keypair_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"deleted": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = DeleteKeypairResourcePolicyRequest(name="default")
        result = await rp.delete_keypair_policy(request)

        assert isinstance(result, DeleteKeypairResourcePolicyResponse)
        assert result.deleted is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/keypair/delete" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default"


class TestUserResourcePolicy:
    @pytest.mark.asyncio
    async def test_create_user_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(return_value={"item": _USER_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = CreateUserResourcePolicyRequest(
            name="default-user",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_session_count_per_model_session=3,
            max_customized_image_count=5,
        )
        result = await rp.create_user_policy(request)

        assert isinstance(result, CreateUserResourcePolicyResponse)
        assert result.item.name == "default-user"
        assert result.item.max_vfolder_count == 10

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/user" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default-user"

    @pytest.mark.asyncio
    async def test_get_user_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": _USER_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        result = await rp.get_user_policy("default-user")

        assert isinstance(result, GetUserResourcePolicyResponse)
        assert result.item.name == "default-user"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/resource-policies/user/default-user" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search_user_policies(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [_USER_POLICY_PAYLOAD],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = SearchUserResourcePoliciesRequest()
        result = await rp.search_user_policies(request)

        assert isinstance(result, SearchUserResourcePoliciesResponse)
        assert len(result.items) == 1
        assert result.pagination.total == 1

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/user/search" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_update_user_policy(self) -> None:
        updated = {**_USER_POLICY_PAYLOAD, "max_vfolder_count": 20}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": updated})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = UpdateUserResourcePolicyRequest(max_vfolder_count=20)
        result = await rp.update_user_policy("default-user", request)

        assert isinstance(result, UpdateUserResourcePolicyResponse)
        assert result.item.max_vfolder_count == 20

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "PATCH"
        assert "/admin/resource-policies/user/default-user" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_delete_user_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"deleted": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = DeleteUserResourcePolicyRequest(name="default-user")
        result = await rp.delete_user_policy(request)

        assert isinstance(result, DeleteUserResourcePolicyResponse)
        assert result.deleted is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/user/delete" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default-user"


class TestProjectResourcePolicy:
    @pytest.mark.asyncio
    async def test_create_project_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(return_value={"item": _PROJECT_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = CreateProjectResourcePolicyRequest(
            name="default-project",
            max_vfolder_count=50,
            max_quota_scope_size=10737418240,
            max_network_count=10,
        )
        result = await rp.create_project_policy(request)

        assert isinstance(result, CreateProjectResourcePolicyResponse)
        assert result.item.name == "default-project"
        assert result.item.max_network_count == 10

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/project" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default-project"

    @pytest.mark.asyncio
    async def test_get_project_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": _PROJECT_POLICY_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        result = await rp.get_project_policy("default-project")

        assert isinstance(result, GetProjectResourcePolicyResponse)
        assert result.item.name == "default-project"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/resource-policies/project/default-project" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search_project_policies(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [_PROJECT_POLICY_PAYLOAD],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = SearchProjectResourcePoliciesRequest()
        result = await rp.search_project_policies(request)

        assert isinstance(result, SearchProjectResourcePoliciesResponse)
        assert len(result.items) == 1
        assert result.pagination.total == 1

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/project/search" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_update_project_policy(self) -> None:
        updated = {**_PROJECT_POLICY_PAYLOAD, "max_network_count": 20}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"item": updated})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = UpdateProjectResourcePolicyRequest(max_network_count=20)
        result = await rp.update_project_policy("default-project", request)

        assert isinstance(result, UpdateProjectResourcePolicyResponse)
        assert result.item.max_network_count == 20

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "PATCH"
        assert "/admin/resource-policies/project/default-project" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_delete_project_policy(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"deleted": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        rp = ResourcePolicyClient(client)

        request = DeleteProjectResourcePolicyRequest(name="default-project")
        result = await rp.delete_project_policy(request)

        assert isinstance(result, DeleteProjectResourcePolicyResponse)
        assert result.deleted is True

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/resource-policies/project/delete" in str(call_args.args[1])
        assert call_args.kwargs["json"]["name"] == "default-project"

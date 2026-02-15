from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.template import TemplateClient
from ai.backend.common.dto.manager.template import (
    CreateClusterTemplateRequest,
    CreateClusterTemplateResponse,
    CreateSessionTemplateRequest,
    CreateSessionTemplateResponse,
    DeleteClusterTemplateRequest,
    DeleteClusterTemplateResponse,
    DeleteSessionTemplateRequest,
    DeleteSessionTemplateResponse,
    GetClusterTemplateRequest,
    GetClusterTemplateResponse,
    GetSessionTemplateRequest,
    GetSessionTemplateResponse,
    ListClusterTemplatesRequest,
    ListClusterTemplatesResponse,
    ListSessionTemplatesRequest,
    ListSessionTemplatesResponse,
    UpdateClusterTemplateRequest,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateRequest,
    UpdateSessionTemplateResponse,
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


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_template_client(mock_session: MagicMock) -> TemplateClient:
    return TemplateClient(_make_client(mock_session))


class TestCreateSessionTemplate:
    @pytest.mark.asyncio
    async def test_sends_post_to_correct_path(self) -> None:
        raw_data = [{"id": "tmpl-1", "user": "user-1"}]
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=raw_data)
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = CreateSessionTemplateRequest(
            payload='{"name": "test"}',
            group="default",
            domain="default",
        )
        result = await client.create_session_template(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/template/session" in str(call_args[0][1])
        assert isinstance(result, CreateSessionTemplateResponse)
        assert result.root[0].id == "tmpl-1"
        assert result.model_dump() == raw_data

    @pytest.mark.asyncio
    async def test_serializes_request_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[{"id": "tmpl-1", "user": "user-1"}])
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = CreateSessionTemplateRequest(
            payload='{"name": "test"}',
            group="mygroup",
            domain="mydomain",
        )
        await client.create_session_template(request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["json"]["payload"] == '{"name": "test"}'
        assert call_kwargs["json"]["group"] == "mygroup"
        assert call_kwargs["json"]["domain"] == "mydomain"


class TestListSessionTemplates:
    @pytest.mark.asyncio
    async def test_sends_get_with_query_params(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = ListSessionTemplatesRequest(all=True)
        result = await client.list_session_templates(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/template/session" in str(call_args[0][1])
        assert call_args.kwargs["params"]["all"] == "True"
        assert isinstance(result, ListSessionTemplatesResponse)

    @pytest.mark.asyncio
    async def test_deserializes_list_response(self) -> None:
        raw_data = [
            {
                "name": "tmpl1",
                "id": "id-1",
                "created_at": "2024-01-01T00:00:00",
                "is_owner": True,
                "user": "u1",
                "group": "g1",
                "user_email": "a@b.com",
                "group_name": "grp",
                "domain_name": "default",
                "type": "user",
                "template": {"key": "val"},
            },
        ]
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=raw_data)
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.list_session_templates(ListSessionTemplatesRequest())
        assert len(result.root) == 1
        assert result.root[0].name == "tmpl1"


class TestGetSessionTemplate:
    @pytest.mark.asyncio
    async def test_interpolates_template_id(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "template": {"key": "val"},
                "name": "test",
                "user_uuid": "u1",
                "group_id": "g1",
                "domain_name": "default",
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.get_session_template("tmpl-123")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/template/session/tmpl-123" in str(call_args[0][1])
        assert isinstance(result, GetSessionTemplateResponse)
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_passes_query_params(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "template": {},
                "name": "test",
                "user_uuid": "u1",
                "group_id": "g1",
                "domain_name": "default",
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = GetSessionTemplateRequest(format="yaml")
        await client.get_session_template("tmpl-123", request=request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["format"] == "yaml"


class TestUpdateSessionTemplate:
    @pytest.mark.asyncio
    async def test_sends_put_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = UpdateSessionTemplateRequest(payload='{"updated": true}')
        result = await client.update_session_template("tmpl-456", request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/template/session/tmpl-456" in str(call_args[0][1])
        assert isinstance(result, UpdateSessionTemplateResponse)
        assert result.success is True


class TestDeleteSessionTemplate:
    @pytest.mark.asyncio
    async def test_sends_delete_with_path_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.delete_session_template("tmpl-789")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/template/session/tmpl-789" in str(call_args[0][1])
        assert isinstance(result, DeleteSessionTemplateResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_passes_owner_access_key_as_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = DeleteSessionTemplateRequest(owner_access_key="AKTEST")
        await client.delete_session_template("tmpl-789", request=request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["owner_access_key"] == "AKTEST"


class TestCreateClusterTemplate:
    @pytest.mark.asyncio
    async def test_sends_post_to_correct_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "ct-1", "user": "u1"})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = CreateClusterTemplateRequest(payload='{"cluster": true}')
        result = await client.create_cluster_template(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/template/cluster" in str(call_args[0][1])
        assert isinstance(result, CreateClusterTemplateResponse)
        assert result.id == "ct-1"


class TestListClusterTemplates:
    @pytest.mark.asyncio
    async def test_sends_get_with_query_params(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = ListClusterTemplatesRequest(all=True)
        result = await client.list_cluster_templates(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/template/cluster" in str(call_args[0][1])
        assert isinstance(result, ListClusterTemplatesResponse)

    @pytest.mark.asyncio
    async def test_deserializes_list_response(self) -> None:
        raw_data = [
            {
                "name": "cluster1",
                "id": "ct-1",
                "created_at": "2024-01-01T00:00:00",
                "is_owner": True,
                "user": "u1",
                "group": "g1",
                "user_email": "a@b.com",
                "group_name": "grp",
                "type": "user",
            },
        ]
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=raw_data)
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.list_cluster_templates(ListClusterTemplatesRequest())
        assert len(result.root) == 1
        assert result.root[0].name == "cluster1"


class TestGetClusterTemplate:
    @pytest.mark.asyncio
    async def test_interpolates_template_id(self) -> None:
        raw_data = {"name": "cluster-tmpl", "nodes": []}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=raw_data)
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.get_cluster_template("ct-123")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/template/cluster/ct-123" in str(call_args[0][1])
        assert isinstance(result, GetClusterTemplateResponse)
        assert result.root["name"] == "cluster-tmpl"
        assert result.model_dump() == raw_data

    @pytest.mark.asyncio
    async def test_passes_format_query_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"data": "yaml-content"})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = GetClusterTemplateRequest(format="json")
        await client.get_cluster_template("ct-123", request=request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["format"] == "json"


class TestUpdateClusterTemplate:
    @pytest.mark.asyncio
    async def test_sends_put_with_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = UpdateClusterTemplateRequest(payload='{"updated": true}')
        result = await client.update_cluster_template("ct-456", request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/template/cluster/ct-456" in str(call_args[0][1])
        assert isinstance(result, UpdateClusterTemplateResponse)
        assert result.success is True


class TestDeleteClusterTemplate:
    @pytest.mark.asyncio
    async def test_sends_delete_with_path_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        result = await client.delete_cluster_template("ct-789")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/template/cluster/ct-789" in str(call_args[0][1])
        assert isinstance(result, DeleteClusterTemplateResponse)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_passes_owner_access_key_as_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_template_client(mock_session)

        request = DeleteClusterTemplateRequest(owner_access_key="AKTEST")
        await client.delete_cluster_template("ct-789", request=request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["owner_access_key"] == "AKTEST"

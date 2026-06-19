from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from yarl import URL

from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.app_config_definition import V2AppConfigDefinitionClient
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
    CreateAppConfigDefinitionPayload,
    PurgeAppConfigDefinitionPayload,
    SearchAppConfigDefinitionsPayload,
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


def _make_client(mock_session: MagicMock) -> V2AppConfigDefinitionClient:
    auth_client = BackendAIAuthClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return V2AppConfigDefinitionClient(auth_client)


def _node_payload(definition_id: str, config_name: str) -> dict[str, str]:
    return {
        "id": definition_id,
        "config_name": config_name,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
    }


class TestAdminCreate:
    async def test_happy_path(self) -> None:
        definition_id = str(uuid4())
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(
            return_value={"app_config_definition": _node_payload(definition_id, "theme")}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_create(CreateAppConfigDefinitionInput(config_name="theme"))

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-definitions/")
        assert call_args.kwargs["json"]["config_name"] == "theme"
        assert isinstance(result, CreateAppConfigDefinitionPayload)
        assert result.app_config_definition.config_name == "theme"


class TestAdminSearch:
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [_node_payload(str(uuid4()), "menu")],
                "total_count": 1,
                "has_next_page": False,
                "has_previous_page": False,
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_search(SearchAppConfigDefinitionsInput(limit=10))

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/v2/app-config-definitions/search" in str(call_args[0][1])
        assert isinstance(result, SearchAppConfigDefinitionsPayload)
        assert [item.config_name for item in result.items] == ["menu"]
        assert result.total_count == 1


class TestAdminGet:
    async def test_happy_path(self) -> None:
        definition_id = uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=_node_payload(str(definition_id), "preferences"))
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_get(definition_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-definitions/{definition_id}")
        assert isinstance(result, AppConfigDefinitionNode)
        assert result.config_name == "preferences"


class TestAdminPurge:
    async def test_happy_path(self) -> None:
        definition_id = uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": str(definition_id)})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_purge(definition_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-definitions/{definition_id}")
        assert isinstance(result, PurgeAppConfigDefinitionPayload)
        assert result.id == definition_id

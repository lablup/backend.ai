from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from yarl import URL

from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.app_config_allow_list import V2AppConfigAllowListClient
from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
    CreateAppConfigAllowListPayload,
    PurgeAppConfigAllowListPayload,
    SearchAppConfigAllowListPayload,
    UpdateAppConfigAllowListPayload,
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


def _make_client(mock_session: MagicMock) -> V2AppConfigAllowListClient:
    auth_client = BackendAIAuthClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return V2AppConfigAllowListClient(auth_client)


def _node_payload(entry_id: str, config_name: str) -> dict[str, str | int]:
    return {
        "id": entry_id,
        "config_name": config_name,
        "scope_type": "domain",
        "rank": 200,
        "read_access": "authenticated",
        "write_access": "admin",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
    }


class TestAdminCreate:
    async def test_happy_path(self) -> None:
        entry_id = str(uuid4())
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"app_config_allow_list": _node_payload(entry_id, "theme")}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_create(
            CreateAppConfigAllowListInput(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
            )
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-allow-list/")
        assert isinstance(result, CreateAppConfigAllowListPayload)
        assert result.app_config_allow_list.config_name == "theme"
        assert result.app_config_allow_list.scope_type == AppConfigScopeType.DOMAIN
        assert result.app_config_allow_list.rank == 200
        assert result.app_config_allow_list.read_access == AppConfigAccessLevel.AUTHENTICATED
        assert result.app_config_allow_list.write_access == AppConfigAccessLevel.ADMIN


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

        result = await client.admin_search(SearchAppConfigAllowListInput(limit=10))

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/v2/app-config-allow-list/search" in str(call_args[0][1])
        assert isinstance(result, SearchAppConfigAllowListPayload)
        assert [item.config_name for item in result.items] == ["menu"]
        assert result.total_count == 1


class TestAdminGet:
    async def test_happy_path(self) -> None:
        entry_id = uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=_node_payload(str(entry_id), "preferences"))
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_get(entry_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-allow-list/{entry_id}")
        assert isinstance(result, AppConfigAllowListNode)
        assert result.config_name == "preferences"


class TestAdminUpdate:
    async def test_happy_path(self) -> None:
        entry_id = uuid4()
        payload = _node_payload(str(entry_id), "theme")
        payload["rank"] = 250
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"app_config_allow_list": payload})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_update(
            entry_id,
            UpdateAppConfigAllowListInput(
                id=entry_id,
                rank=250,
                write_access=AppConfigAccessLevel.OWNER,
            ),
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-allow-list/{entry_id}")
        assert isinstance(result, UpdateAppConfigAllowListPayload)
        assert result.app_config_allow_list.rank == 250
        # response access tiers round-trip through the typed response model
        assert result.app_config_allow_list.read_access == AppConfigAccessLevel.AUTHENTICATED
        assert result.app_config_allow_list.write_access == AppConfigAccessLevel.ADMIN


class TestAdminPurge:
    async def test_happy_path(self) -> None:
        entry_id = uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": str(entry_id)})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.admin_purge(entry_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-allow-list/{entry_id}")
        assert isinstance(result, PurgeAppConfigAllowListPayload)
        assert result.id == entry_id

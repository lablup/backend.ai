from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.auth import NoAuth
from ai.backend.client.v2.base_client import BackendAIAnonymousClient, BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.app_config import V2AppConfigClient
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


@dataclass(frozen=True)
class _MergedReadCase:
    """One of the two merged reads: the same batch shape over a different HTTP client."""

    method_name: str
    path: str
    input_type: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]
    signed: bool


@pytest.fixture
def payload_json() -> dict[str, Any]:
    """The merged answer as the server sends it: one merged name, one nothing contributed to."""
    return {
        "app_configs": [
            {
                "config_name": "theme",
                "merged_config": {"mode": "dark"},
                "fragments": [
                    {
                        "id": str(uuid4()),
                        "config_name": "theme",
                        "scope_type": AppConfigScopeType.PUBLIC.value,
                        "scope_id": None,
                        "config": {"mode": "light"},
                        "created_at": "2026-01-01T00:00:00+00:00",
                        "updated_at": "2026-01-01T00:00:00+00:00",
                    },
                    {
                        "id": str(uuid4()),
                        "config_name": "theme",
                        "scope_type": AppConfigScopeType.USER.value,
                        "scope_id": str(uuid4()),
                        "config": {"mode": "dark"},
                        "created_at": "2026-01-02T00:00:00+00:00",
                        "updated_at": "2026-01-02T00:00:00+00:00",
                    },
                ],
            },
            {"config_name": "menu", "merged_config": {}, "fragments": []},
        ]
    }


@pytest.fixture
def mock_response(payload_json: dict[str, Any]) -> AsyncMock:
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value=payload_json)
    return response


@pytest.fixture
def mock_session(mock_response: AsyncMock) -> MagicMock:
    request_ctx = AsyncMock()
    request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    request_ctx.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.request = MagicMock(return_value=request_ctx)
    return session


@pytest.fixture
def client(mock_session: MagicMock) -> V2AppConfigClient:
    """Both halves of the client share one session mock, so either call lands in the same spy."""
    return V2AppConfigClient(
        BackendAIAuthClient(_DEFAULT_CONFIG, MockAuth(), mock_session),
        BackendAIAnonymousClient(_DEFAULT_CONFIG, mock_session),
    )


@pytest.mark.parametrize(
    "case",
    [
        _MergedReadCase(
            method_name="my_get_app_configs",
            path="/v2/app-config/my/get",
            input_type=MyGetAppConfigsInput,
            signed=True,
        ),
        _MergedReadCase(
            method_name="public_get_app_configs",
            path="/v2/app-config/public/get",
            input_type=PublicGetAppConfigsInput,
            signed=False,
        ),
    ],
    ids=lambda case: case.method_name,
)
class TestMergedRead:
    async def test_posts_to_its_own_path_and_parses_the_payload(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
        mock_session: MagicMock,
    ) -> None:
        result = await getattr(client, case.method_name)(
            case.input_type(config_names=["theme", "menu"])
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith(case.path)
        assert call_args[1]["json"] == {"config_names": ["theme", "menu"]}
        assert isinstance(result, GetAppConfigsPayload)
        assert [node.config_name for node in result.app_configs] == ["theme", "menu"]

    async def test_returns_the_merge_and_its_contributing_fragments(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
    ) -> None:
        result = await getattr(client, case.method_name)(
            case.input_type(config_names=["theme", "menu"])
        )

        merged, uncontributed = result.app_configs
        assert merged.merged_config == {"mode": "dark"}
        assert [f.scope_type for f in merged.fragments] == [
            AppConfigScopeType.PUBLIC,
            AppConfigScopeType.USER,
        ]
        assert uncontributed.merged_config == {}
        assert uncontributed.fragments == []

    async def test_only_the_authenticated_read_is_signed(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
        mock_session: MagicMock,
    ) -> None:
        """The public read must reach the server without credentials — that is its whole point."""
        await getattr(client, case.method_name)(case.input_type(config_names=["theme"]))

        headers = mock_session.request.call_args[1]["headers"]
        assert ("Authorization" in headers) is case.signed


class TestPreLoginCaller:
    async def test_a_caller_holding_no_credentials_can_make_the_public_read(
        self,
        mock_session: MagicMock,
    ) -> None:
        """The pre-login case end to end: build the registry with no keypair and read.

        ``NoAuth`` is what a caller has before it holds any credentials, so reaching the
        public read through the registry with it is the contract this endpoint exists for.
        """
        registry = V2ClientRegistry(
            BackendAIAuthClient(_DEFAULT_CONFIG, NoAuth(), mock_session),
            BackendAIAnonymousClient(_DEFAULT_CONFIG, mock_session),
        )

        result = await registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme", "menu"])
        )

        assert "Authorization" not in mock_session.request.call_args[1]["headers"]
        assert [node.config_name for node in result.app_configs] == ["theme", "menu"]

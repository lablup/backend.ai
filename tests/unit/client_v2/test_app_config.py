from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.auth import NoAuth
from ai.backend.client.v2.base_client import BackendAIAnonymousClient, BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.app_config import V2AppConfigClient
from ai.backend.client.v2.v2_registry import V2ClientRegistry
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

    read: Callable[[V2AppConfigClient, Any], Awaitable[GetAppConfigsPayload]]
    path: str
    input_type: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]
    signed: bool


@pytest.fixture
def payload_json() -> dict[str, Any]:
    """The merged answer as the server sends it: one merged name, one nothing contributed to."""
    return {
        "app_configs": [
            {"config_name": "theme", "config": {"mode": "dark"}},
            {"config_name": "menu", "config": {}},
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


@pytest.fixture
def pre_login_registry(mock_session: MagicMock) -> V2ClientRegistry:
    """A registry as a caller holds it before it has any credentials.

    ``NoAuth`` is what the authenticated half carries until a keypair is configured.
    """
    return V2ClientRegistry(
        BackendAIAuthClient(_DEFAULT_CONFIG, NoAuth(), mock_session),
        BackendAIAnonymousClient(_DEFAULT_CONFIG, mock_session),
    )


@pytest.mark.parametrize(
    "case",
    [
        _MergedReadCase(
            read=V2AppConfigClient.my_get_app_configs,
            path="/v2/app-config/my/get",
            input_type=MyGetAppConfigsInput,
            signed=True,
        ),
        _MergedReadCase(
            read=V2AppConfigClient.public_get_app_configs,
            path="/v2/app-config/public/get",
            input_type=PublicGetAppConfigsInput,
            signed=False,
        ),
    ],
    ids=lambda case: case.read.__name__,
)
class TestMergedRead:
    async def test_posts_to_its_own_path_and_parses_the_payload(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
        mock_session: MagicMock,
    ) -> None:
        result = await case.read(client, case.input_type(config_names=["theme", "menu"]))

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith(case.path)
        assert call_args[1]["json"] == {"config_names": ["theme", "menu"]}
        assert isinstance(result, GetAppConfigsPayload)
        assert [node.config_name for node in result.app_configs] == ["theme", "menu"]

    async def test_returns_the_merge_for_each_requested_name(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
    ) -> None:
        result = await case.read(client, case.input_type(config_names=["theme", "menu"]))

        merged, uncontributed = result.app_configs
        assert merged.config == {"mode": "dark"}
        assert uncontributed.config == {}

    async def test_only_the_authenticated_read_is_signed(
        self,
        case: _MergedReadCase,
        client: V2AppConfigClient,
        mock_session: MagicMock,
    ) -> None:
        """The public read must reach the server without credentials — that is its whole point."""
        await case.read(client, case.input_type(config_names=["theme"]))

        headers = mock_session.request.call_args[1]["headers"]
        assert ("Authorization" in headers) is case.signed


class TestPreLoginCaller:
    async def test_a_caller_holding_no_credentials_can_make_the_public_read(
        self,
        pre_login_registry: V2ClientRegistry,
        mock_session: MagicMock,
    ) -> None:
        """Reaching the public read through the registry is the contract it exists for."""
        result = await pre_login_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme", "menu"])
        )

        assert "Authorization" not in mock_session.request.call_args[1]["headers"]
        assert [node.config_name for node in result.app_configs] == ["theme", "menu"]

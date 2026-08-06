from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

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
def registry(mock_session: MagicMock) -> V2ClientRegistry:
    """A registry that does hold credentials, so a signed call is told apart from an unsigned one."""
    return V2ClientRegistry(
        BackendAIAuthClient(_DEFAULT_CONFIG, MockAuth(), mock_session),
        BackendAIAnonymousClient(_DEFAULT_CONFIG, mock_session),
    )


class TestMyMergedRead:
    async def test_posts_to_its_own_path(
        self, client: V2AppConfigClient, mock_session: MagicMock
    ) -> None:
        await client.my_get_app_configs(MyGetAppConfigsInput(config_names=["theme", "menu"]))

        method, url = mock_session.request.call_args[0][:2]
        assert method == "POST"
        assert str(url).endswith("/v2/app-config/my/get")
        assert mock_session.request.call_args[1]["json"] == {"config_names": ["theme", "menu"]}

    async def test_is_signed(self, client: V2AppConfigClient, mock_session: MagicMock) -> None:
        await client.my_get_app_configs(MyGetAppConfigsInput(config_names=["theme"]))

        assert "Authorization" in mock_session.request.call_args[1]["headers"]

    async def test_parses_the_merge_for_each_requested_name(
        self, client: V2AppConfigClient
    ) -> None:
        result = await client.my_get_app_configs(
            MyGetAppConfigsInput(config_names=["theme", "menu"])
        )

        assert isinstance(result, GetAppConfigsPayload)
        merged, uncontributed = result.app_configs
        assert (merged.config_name, merged.config) == ("theme", {"mode": "dark"})
        assert (uncontributed.config_name, uncontributed.config) == ("menu", {})


class TestPublicMergedRead:
    async def test_posts_to_its_own_path(
        self, client: V2AppConfigClient, mock_session: MagicMock
    ) -> None:
        await client.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme", "menu"])
        )

        method, url = mock_session.request.call_args[0][:2]
        assert method == "POST"
        assert str(url).endswith("/v2/app-config/public/get")
        assert mock_session.request.call_args[1]["json"] == {"config_names": ["theme", "menu"]}

    async def test_is_not_signed(self, client: V2AppConfigClient, mock_session: MagicMock) -> None:
        """The public read must reach the server without credentials — that is its whole point."""
        await client.public_get_app_configs(PublicGetAppConfigsInput(config_names=["theme"]))

        assert "Authorization" not in mock_session.request.call_args[1]["headers"]

    async def test_parses_the_merge_for_each_requested_name(
        self, client: V2AppConfigClient
    ) -> None:
        result = await client.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme", "menu"])
        )

        assert isinstance(result, GetAppConfigsPayload)
        merged, uncontributed = result.app_configs
        assert (merged.config_name, merged.config) == ("theme", {"mode": "dark"})
        assert (uncontributed.config_name, uncontributed.config) == ("menu", {})


class TestRegistryWiring:
    async def test_hands_the_public_read_the_anonymous_client(
        self,
        registry: V2ClientRegistry,
        mock_session: MagicMock,
    ) -> None:
        """A caller holding credentials still reaches the public read without sending them.

        The registry keeps both halves, so wiring this domain to the authenticated one would
        sign the pre-login read.
        """
        await registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme"])
        )

        assert "Authorization" not in mock_session.request.call_args[1]["headers"]

from __future__ import annotations

from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl
from aiohttp import web
from pytest_mock import MockerFixture

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.web.auth import get_anonymous_session, get_api_session
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint

from .conftest import DummyApiConfig, DummyConfig

DEFAULT_ENDPOINT = "https://api.backend.ai"
ALTERNATIVE_ENDPOINT = "https://alternative.backend.ai"


class DummyRequest:
    def __init__(self, app_data: dict[str, Any]) -> None:
        self.app = app_data


@pytest.fixture
async def client_pool() -> ClientPool:
    factory = partial(
        tcp_client_session_factory,
        ssl=False,
        limit=10,
        limit_per_host=5,
    )
    return ClientPool(factory, cleanup_interval_seconds=100)


@pytest.fixture
async def mock_request(client_pool: ClientPool) -> DummyRequest:
    return DummyRequest({
        "config": DummyConfig(DummyApiConfig(endpoint=[yarl.URL(DEFAULT_ENDPOINT)])),
        "client_pool": client_pool,
    })


class TestGetApiSession:
    async def test_requires_authenticated_session(
        self, mocker: MockerFixture, mock_request: DummyRequest
    ) -> None:
        get_session = AsyncMock(return_value={"authenticated": False})
        mocker.patch("ai.backend.web.auth.get_session", get_session)
        with pytest.raises(web.HTTPUnauthorized):
            await get_api_session(mock_request, AcquiredEndpoint(endpoint=DEFAULT_ENDPOINT))  # type: ignore
        get_session.assert_awaited_once()

    async def test_rejects_non_keypair_token(
        self, mocker: MockerFixture, mock_request: DummyRequest
    ) -> None:
        get_session = AsyncMock(
            return_value={"authenticated": True, "token": {"type": "something-else"}}
        )
        mocker.patch("ai.backend.web.auth.get_session", get_session)
        with pytest.raises(web.HTTPBadRequest):
            await get_api_session(mock_request, AcquiredEndpoint(endpoint=DEFAULT_ENDPOINT))  # type: ignore
        get_session.assert_awaited_once()

    @pytest.mark.parametrize("acquired_endpoint", [DEFAULT_ENDPOINT, ALTERNATIVE_ENDPOINT])
    async def test_returns_keypair_session_at_acquired_endpoint(
        self, mocker: MockerFixture, mock_request: DummyRequest, acquired_endpoint: str
    ) -> None:
        get_session = AsyncMock(
            return_value={
                "authenticated": True,
                "token": {"type": "keypair", "access_key": "ABC", "secret_key": "xyz"},
            }
        )
        mocker.patch("ai.backend.web.auth.get_session", get_session)
        api_session = await get_api_session(
            mock_request,  # type: ignore
            AcquiredEndpoint(endpoint=acquired_endpoint),
        )
        get_session.assert_awaited_once()
        async with api_session:
            assert not api_session.config.is_anonymous
            assert api_session.config.domain == "default"
            assert str(api_session.config.endpoint) == acquired_endpoint
            assert api_session.config.access_key == "ABC"
            assert api_session.config.secret_key == "xyz"


class TestGetAnonymousSession:
    @pytest.mark.parametrize("acquired_endpoint", [DEFAULT_ENDPOINT, ALTERNATIVE_ENDPOINT])
    async def test_returns_anonymous_session_at_acquired_endpoint(
        self, mocker: MockerFixture, mock_request: DummyRequest, acquired_endpoint: str
    ) -> None:
        get_session = MagicMock()
        mocker.patch("ai.backend.web.auth.get_session", get_session)
        api_session = await get_anonymous_session(
            mock_request,  # type: ignore
            AcquiredEndpoint(endpoint=acquired_endpoint),
        )
        get_session.assert_not_called()
        async with api_session:
            assert api_session.config.is_anonymous
            assert api_session.config.domain == "default"
            assert str(api_session.config.endpoint) == acquired_endpoint
            assert api_session.config.access_key == ""
            assert api_session.config.secret_key == ""

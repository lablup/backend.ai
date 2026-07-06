from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl
from aiohttp import web
from pytest_mock import MockerFixture

from ai.backend.web import server
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint
from ai.backend.web.config.unified import WebServerUnifiedConfig

from .conftest import DummyApiConfig, DummyConfig


class _FakeAPISession:
    """Stand-in for the SDK ``AsyncSession`` used inside the anonymous-auth helper."""

    def __init__(self, *, config: Any) -> None:
        self.config = config
        self.aiohttp_session = MagicMock()
        self.User = MagicMock()
        self.User.authorize = AsyncMock()

    async def __aenter__(self) -> _FakeAPISession:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False


def _web_config(endpoints: list[str]) -> WebServerUnifiedConfig:
    config = DummyConfig(DummyApiConfig(endpoint=[yarl.URL(e) for e in endpoints]))
    return cast(WebServerUnifiedConfig, config)


@pytest.fixture
def acquired_endpoint() -> AcquiredEndpoint:
    """A healthy endpoint the caller acquired from the pool."""
    return AcquiredEndpoint(endpoint="https://m2")


def _patch_apisession(mocker: MockerFixture, *, auth_result: object) -> dict[str, Any]:
    """Patch ``server.APISession`` with a capturing fake and return the capture dict."""
    captured: dict[str, Any] = {}

    def _factory(*, config: Any) -> _FakeAPISession:
        session = _FakeAPISession(config=config)
        session.User.authorize.return_value = auth_result
        captured["config"] = config
        captured["session"] = session
        return session

    mocker.patch.object(server, "APISession", _factory)
    mocker.patch.object(server, "fill_forwarding_hdrs_to_api_session")
    return captured


class TestAuthorizeViaAnonymousSession:
    async def test_uses_acquired_endpoint(
        self, mocker: MockerFixture, acquired_endpoint: AcquiredEndpoint
    ) -> None:
        auth_result = object()
        captured = _patch_apisession(mocker, auth_result=auth_result)

        result = await server._authorize_via_anonymous_session(
            cast(web.Request, MagicMock()),
            acquired_endpoint,
            _web_config(["https://m1", "https://m2"]),
            username="user",
            password="pass",
            extra_args={"otp": "123"},
        )

        assert result is auth_result
        # The anonymous config targets the acquired endpoint, not endpoint[0].
        assert str(captured["config"].endpoint) == "https://m2"
        assert captured["config"].is_anonymous
        captured["session"].User.authorize.assert_awaited_once_with(
            "user", "pass", extra_args={"otp": "123"}
        )

    async def test_forwards_cookies_when_requested(
        self, mocker: MockerFixture, acquired_endpoint: AcquiredEndpoint
    ) -> None:
        captured = _patch_apisession(mocker, auth_result=object())
        request = MagicMock()
        request.cookies = {"sToken": "abc"}

        await server._authorize_via_anonymous_session(
            cast(web.Request, request),
            acquired_endpoint,
            _web_config(["https://m1"]),
            username="fake",
            password="fake",
            extra_args={},
            forward_cookies=True,
        )

        captured["session"].aiohttp_session.cookie_jar.update_cookies.assert_called_once_with(
            request.cookies
        )

    async def test_does_not_forward_cookies_by_default(
        self, mocker: MockerFixture, acquired_endpoint: AcquiredEndpoint
    ) -> None:
        captured = _patch_apisession(mocker, auth_result=object())

        await server._authorize_via_anonymous_session(
            cast(web.Request, MagicMock()),
            acquired_endpoint,
            _web_config(["https://m1"]),
            username="user",
            password="pass",
            extra_args={},
        )

        captured["session"].aiohttp_session.cookie_jar.update_cookies.assert_not_called()


class TestNoAuthClientRegistriesCtx:
    def _patch_create(self, mocker: MockerFixture) -> dict[str, MagicMock]:
        registries_by_endpoint: dict[str, MagicMock] = {}

        def _create(config: Any, auth: Any) -> MagicMock:
            registry = MagicMock()
            registry.close = AsyncMock()
            registries_by_endpoint[str(config.endpoint)] = registry
            return registry

        mocker.patch(
            "ai.backend.web.server.BackendAIClientRegistry.create",
            AsyncMock(side_effect=_create),
        )
        return registries_by_endpoint

    async def test_builds_one_registry_per_endpoint(self, mocker: MockerFixture) -> None:
        registries_by_endpoint = self._patch_create(mocker)

        async with server.no_auth_client_registries_ctx(
            _web_config(["https://m1", "https://m2", "https://m3"])
        ) as registries:
            assert set(registries.keys()) == {"https://m1", "https://m2", "https://m3"}
            assert len(registries_by_endpoint) == 3
            # Each registry is keyed by the endpoint it was built for, so the
            # handler can look it up by the endpoint the pool hands out.
            for key, registry in registries.items():
                assert registry is registries_by_endpoint[key]

    async def test_closes_all_registries_on_exit(self, mocker: MockerFixture) -> None:
        registries_by_endpoint = self._patch_create(mocker)

        async with server.no_auth_client_registries_ctx(_web_config(["https://m1", "https://m2"])):
            pass

        assert len(registries_by_endpoint) == 2
        for registry in registries_by_endpoint.values():
            registry.close.assert_awaited_once()

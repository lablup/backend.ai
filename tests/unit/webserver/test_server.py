from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl
from aiohttp import web
from pytest_mock import MockerFixture

from ai.backend.web import server
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint, HealthyEndpointPool
from ai.backend.web.config.unified import WebServerUnifiedConfig
from ai.backend.web.errors import ManagerConnectionUnavailable

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


def _make_manager_pool(
    *, endpoint: str | None = None, raises: Exception | None = None
) -> HealthyEndpointPool:
    pool = MagicMock()

    @asynccontextmanager
    async def _acquire() -> Any:
        if raises is not None:
            raise raises
        assert endpoint is not None
        yield AcquiredEndpoint(endpoint=endpoint)

    pool.acquire = _acquire
    return cast(HealthyEndpointPool, pool)


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
    async def test_uses_endpoint_acquired_from_pool(self, mocker: MockerFixture) -> None:
        auth_result = object()
        captured = _patch_apisession(mocker, auth_result=auth_result)
        # The pool hands out the second endpoint (the first is assumed down).
        pool = _make_manager_pool(endpoint="https://m2")

        result = await server._authorize_via_anonymous_session(
            cast(web.Request, MagicMock()),
            pool,
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

    async def test_forwards_cookies_when_requested(self, mocker: MockerFixture) -> None:
        captured = _patch_apisession(mocker, auth_result=object())
        pool = _make_manager_pool(endpoint="https://m1")
        request = MagicMock()
        request.cookies = {"sToken": "abc"}

        await server._authorize_via_anonymous_session(
            cast(web.Request, request),
            pool,
            _web_config(["https://m1"]),
            username="fake",
            password="fake",
            extra_args={},
            forward_cookies=True,
        )

        captured["session"].aiohttp_session.cookie_jar.update_cookies.assert_called_once_with(
            request.cookies
        )

    async def test_does_not_forward_cookies_by_default(self, mocker: MockerFixture) -> None:
        captured = _patch_apisession(mocker, auth_result=object())
        pool = _make_manager_pool(endpoint="https://m1")

        await server._authorize_via_anonymous_session(
            cast(web.Request, MagicMock()),
            pool,
            _web_config(["https://m1"]),
            username="user",
            password="pass",
            extra_args={},
        )

        captured["session"].aiohttp_session.cookie_jar.update_cookies.assert_not_called()

    async def test_propagates_when_no_healthy_endpoint(self, mocker: MockerFixture) -> None:
        _patch_apisession(mocker, auth_result=object())
        pool = _make_manager_pool(raises=ManagerConnectionUnavailable("no healthy endpoint"))

        with pytest.raises(ManagerConnectionUnavailable):
            await server._authorize_via_anonymous_session(
                cast(web.Request, MagicMock()),
                pool,
                _web_config(["https://m1"]),
                username="user",
                password="pass",
                extra_args={},
            )


class TestNoAuthClientRegistriesCtx:
    def _patch_create(self, mocker: MockerFixture) -> list[MagicMock]:
        created: list[MagicMock] = []

        def _create(config: Any, auth: Any) -> MagicMock:
            registry = MagicMock()
            registry.close = AsyncMock()
            registry.endpoint = str(config.endpoint)
            created.append(registry)
            return registry

        mocker.patch.object(
            server.BackendAIClientRegistry, "create", AsyncMock(side_effect=_create)
        )
        return created

    async def test_builds_one_registry_per_endpoint(self, mocker: MockerFixture) -> None:
        created = self._patch_create(mocker)

        async with server.no_auth_client_registries_ctx(
            _web_config(["https://m1", "https://m2", "https://m3"])
        ) as registries:
            assert set(registries.keys()) == {"https://m1", "https://m2", "https://m3"}
            assert len(created) == 3
            # Each registry is keyed by the endpoint it was built for, so the
            # handler can look it up by the endpoint the pool hands out.
            for key, registry in registries.items():
                assert registry.endpoint == key

    async def test_closes_all_registries_on_exit(self, mocker: MockerFixture) -> None:
        created = self._patch_create(mocker)

        async with server.no_auth_client_registries_ctx(_web_config(["https://m1", "https://m2"])):
            pass

        assert len(created) == 2
        for registry in created:
            registry.close.assert_awaited_once()

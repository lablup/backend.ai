from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp_cors
import pytest
from aiohttp import web

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.dto.manager.auth.response import UpdatePasswordNoAuthResponse
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.web.config.unified import SecurityConfig
from ai.backend.web.server import build_cors_options, update_password_no_auth

MANAGER_ENDPOINT = "http://manager:8081"
PASSWORD_UPDATE_BODY = {
    "username": "user@example.com",
    "current_password": "old-password",
    "new_password": "new-password",
}


def _build_app(update_password: AsyncMock) -> web.Application:
    acquired = MagicMock()
    acquired.endpoint = MANAGER_ENDPOINT

    @asynccontextmanager
    async def acquire() -> AsyncIterator[MagicMock]:
        yield acquired

    manager_pool = MagicMock()
    manager_pool.acquire = acquire
    registry = MagicMock()
    registry.auth.update_password_no_auth = update_password

    app = web.Application()
    config = MagicMock()
    config.api.domain = "default"
    app["config"] = config
    app["manager_pool"] = manager_pool
    app["no_auth_client_registries"] = {MANAGER_ENDPOINT: registry}
    app.router.add_route("POST", "/server/update-password-no-auth", update_password_no_auth)
    return app


@pytest.mark.parametrize("status", [400, 401])
async def test_update_password_no_auth_returns_manager_status_on_rejection(
    aiohttp_client: Any, status: int
) -> None:
    update_password = AsyncMock(
        side_effect=BackendAPIError(
            status,
            "Rejected",
            {
                "type": "https://api.backend.ai/probs/rejected",
                "title": "Rejected",
                "msg": "password rejected",
            },
        )
    )
    client = await aiohttp_client(_build_app(update_password))

    resp = await client.post("/server/update-password-no-auth", json=PASSWORD_UPDATE_BODY)

    assert resp.status == status
    assert await resp.json() == {
        "data": {
            "type": "https://api.backend.ai/probs/rejected",
            "title": "Rejected",
            "details": "password rejected",
        },
        "password_changed_at": None,
    }


async def test_update_password_no_auth_returns_200_on_success(aiohttp_client: Any) -> None:
    update_password = AsyncMock(
        return_value=UpdatePasswordNoAuthResponse(password_changed_at="2026-09-29T00:00:00+00:00")
    )
    client = await aiohttp_client(_build_app(update_password))

    resp = await client.post("/server/update-password-no-auth", json=PASSWORD_UPDATE_BODY)

    assert resp.status == 200
    assert await resp.json() == {
        "data": None,
        "password_changed_at": "2026-09-29T00:00:00+00:00",
    }


ALLOWED_ORIGIN = "https://console.example.com"
OTHER_ORIGIN = "https://other.example.com"
PREFLIGHT_METHOD_HEADER = {"Access-Control-Request-Method": "POST"}


async def _cors_client(aiohttp_client: Any, allowed_origins: list[str]) -> Any:
    async def handler(_request: web.Request) -> web.Response:
        return web.json_response({})

    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults=build_cors_options(allowed_origins))
    cors.add(app.router.add_route("POST", "/server/login-check", handler))
    return await aiohttp_client(app)


class TestCorsOptions:
    async def test_allowed_origin_receives_cors_headers(self, aiohttp_client: Any) -> None:
        client = await _cors_client(aiohttp_client, [ALLOWED_ORIGIN])

        resp = await client.post("/server/login-check", headers={"Origin": ALLOWED_ORIGIN})

        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert resp.headers["Access-Control-Allow-Credentials"] == "true"

    async def test_allowed_origin_passes_preflight(self, aiohttp_client: Any) -> None:
        client = await _cors_client(aiohttp_client, [ALLOWED_ORIGIN])

        resp = await client.options(
            "/server/login-check",
            headers={"Origin": ALLOWED_ORIGIN, **PREFLIGHT_METHOD_HEADER},
        )

        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert resp.headers["Access-Control-Allow-Credentials"] == "true"

    @pytest.mark.parametrize("allowed_origins", [[ALLOWED_ORIGIN], []], ids=["other", "empty"])
    async def test_unlisted_origin_receives_no_cors_headers(
        self, aiohttp_client: Any, allowed_origins: list[str]
    ) -> None:
        client = await _cors_client(aiohttp_client, allowed_origins)

        resp = await client.post("/server/login-check", headers={"Origin": OTHER_ORIGIN})

        assert resp.status == 200
        assert "Access-Control-Allow-Origin" not in resp.headers
        assert "Access-Control-Allow-Credentials" not in resp.headers

    @pytest.mark.parametrize("allowed_origins", [[ALLOWED_ORIGIN], []], ids=["other", "empty"])
    async def test_unlisted_origin_fails_preflight(
        self, aiohttp_client: Any, allowed_origins: list[str]
    ) -> None:
        client = await _cors_client(aiohttp_client, allowed_origins)

        resp = await client.options(
            "/server/login-check",
            headers={"Origin": OTHER_ORIGIN, **PREFLIGHT_METHOD_HEADER},
        )

        assert resp.status == 403
        assert "Access-Control-Allow-Origin" not in resp.headers

    async def test_request_without_origin_receives_no_cors_headers(
        self, aiohttp_client: Any
    ) -> None:
        client = await _cors_client(aiohttp_client, [ALLOWED_ORIGIN])

        resp = await client.post("/server/login-check")

        assert resp.status == 200
        assert "Access-Control-Allow-Origin" not in resp.headers


class TestCorsAllowedOriginsConfig:
    async def test_default_is_empty(self) -> None:
        assert SecurityConfig.model_validate({}).cors_allowed_origins == []

    @pytest.mark.parametrize(
        "origin",
        [ALLOWED_ORIGIN, "http://localhost:9081", "http://[::1]:9081"],
    )
    async def test_accepts_origin_from_toml_alias(self, origin: str) -> None:
        config = SecurityConfig.model_validate({"cors-allowed-origins": [origin]})
        assert config.cors_allowed_origins == [origin]

    @pytest.mark.parametrize(
        "origin",
        [
            "*",
            "null",
            "",
            "https://*.example.com",
            "https://console.example.com/",
            "https://console.example.com/path",
            "https://user@console.example.com",
            "https://console.example.com?query",
            "https://Console.example.com",
            "HTTPS://console.example.com",
            "console.example.com",
            "https://console.example.com\n",
        ],
    )
    async def test_rejects_invalid_origin(self, origin: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            SecurityConfig.model_validate({"cors-allowed-origins": [origin]})

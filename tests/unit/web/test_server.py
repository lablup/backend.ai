import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp_cors
import pytest
import tomli
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.dto.manager.auth.response import UpdatePasswordNoAuthResponse
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.web.session import SESSION_KEY, Session, SimpleCookieStorage, get_session
from ai.backend.common.web.session import setup as setup_session
from ai.backend.web.config.unified import SecurityConfig, WebServerUnifiedConfig
from ai.backend.web.errors import UnauthenticatedError
from ai.backend.web.server import (
    build_cors_options,
    config_toml_handler,
    extend_login_session,
    update_password_no_auth,
    version_json_handler,
)
from ai.backend.web.template import build_template_environment

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


class TestExtendLoginSession:
    @pytest.fixture
    def current_time(self, monkeypatch: pytest.MonkeyPatch) -> int:
        current = 2_000_000_000
        monkeypatch.setattr("ai.backend.web.server.get_time", lambda: current)
        return current

    @pytest.fixture
    def session(self, current_time: int) -> Session:
        session = Session(None, data=None, new=True)
        session.expiration_dt = current_time + 60
        return session

    @pytest.fixture
    def authenticated_session(self, session: Session) -> Session:
        session["authenticated"] = True
        return session

    @pytest.fixture
    def extension_request(self, session: Session) -> web.Request:
        app = web.Application()
        app["config"] = MagicMock(session=MagicMock(login_session_extension_sec=3600))
        request = make_mocked_request("POST", "/server/extend-login-session", app=app)
        request[SESSION_KEY] = session
        return request

    async def test_rejects_unauthenticated_session(
        self, extension_request: web.Request, session: Session
    ) -> None:
        original_expiration = session.expiration_dt

        with pytest.raises(UnauthenticatedError) as exc_info:
            await extend_login_session(extension_request)

        error = exc_info.value
        assert error.status == 401
        assert error.content_type == "application/problem+json"
        assert error.text is not None
        assert json.loads(error.text) == {
            "type": "https://api.backend.ai/probs/auth-failed",
            "title": "Unauthorized access",
            "error_code": "auth_auth_unauthorized",
        }
        assert session.expiration_dt == original_expiration

    async def test_extends_authenticated_session(
        self, extension_request: web.Request, authenticated_session: Session, current_time: int
    ) -> None:
        resp = await extend_login_session(extension_request)

        assert resp.status == 200
        assert authenticated_session.expiration_dt == current_time + 3600
        assert resp.text is not None
        assert json.loads(resp.text) == {
            "status": 201,
            "expires": datetime.fromtimestamp(current_time + 3600, tz=UTC).isoformat(),
        }


ALLOWED_ORIGIN = "https://console.example.com"
OTHER_ORIGIN = "https://other.example.com"
PREFLIGHT_METHOD_HEADER = {"Access-Control-Request-Method": "POST"}


async def _cors_client(
    aiohttp_client: Any, allowed_origins: list[str], *, allow_all_origins: bool = False
) -> Any:
    async def handler(_request: web.Request) -> web.Response:
        return web.json_response({})

    app = web.Application()
    cors = aiohttp_cors.setup(
        app,
        defaults=build_cors_options(allowed_origins, allow_all_origins=allow_all_origins),
    )
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


class TestCorsAllowAllOptions:
    async def test_unlisted_origin_receives_cors_headers(self, aiohttp_client: Any) -> None:
        client = await _cors_client(aiohttp_client, [], allow_all_origins=True)

        resp = await client.post("/server/login-check", headers={"Origin": OTHER_ORIGIN})

        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == OTHER_ORIGIN
        assert resp.headers["Access-Control-Allow-Credentials"] == "true"

    async def test_unlisted_origin_passes_preflight(self, aiohttp_client: Any) -> None:
        client = await _cors_client(aiohttp_client, [], allow_all_origins=True)

        resp = await client.options(
            "/server/login-check",
            headers={"Origin": OTHER_ORIGIN, **PREFLIGHT_METHOD_HEADER},
        )

        assert resp.status == 200
        assert resp.headers["Access-Control-Allow-Origin"] == OTHER_ORIGIN
        assert resp.headers["Access-Control-Allow-Credentials"] == "true"


class TestCorsAllowedOriginsConfig:
    async def test_default_is_empty(self) -> None:
        assert SecurityConfig.model_validate({}).cors_allowed_origins == []

    async def test_allow_all_origins_default_is_false(self) -> None:
        assert SecurityConfig.model_validate({}).cors_allow_all_origins is False

    @pytest.mark.parametrize(
        ("raw_config", "expected"),
        [
            ({"cors-allow-all-origins": True}, True),
            ({"cors_allow_all_origins": True}, True),
            ({"cors-allow-all-origins": False}, False),
        ],
    )
    async def test_accepts_allow_all_origins(
        self, raw_config: dict[str, bool], expected: bool
    ) -> None:
        config = SecurityConfig.model_validate(raw_config)
        assert config.cors_allow_all_origins is expected

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


LOGIN_SCREEN_FIELDS = {
    "apiEndpoint",
    "apiDomainName",
    "connectionMode",
    "signupSupport",
    "allowChangeSigninMode",
    "allowAnonymousChangePassword",
    "allowSignupWithoutConfirmation",
    "singleSignOnVendors",
    "ssoRealmName",
    "enableInteractiveLoginAccountSwitch",
}


async def _login(request: web.Request) -> web.Response:
    session = await get_session(request)
    session["authenticated"] = True
    return web.Response()


class TestConfigTomlHandler:
    @pytest.fixture
    def app(self) -> web.Application:
        app = web.Application()
        setup_session(app, SimpleCookieStorage())
        app["config"] = WebServerUnifiedConfig.model_validate({
            "service": {
                "sso-realm-name": "corp",
                "single-sign-on-vendors": "saml",
                "hide-agents": False,
            },
            "ui": {"menu-blocklist": "agent"},
        })
        app["j2env"] = build_template_environment()
        app.router.add_route("GET", "/config.toml", config_toml_handler)
        app.router.add_route("POST", "/login", _login)
        return app

    async def test_before_login_only_the_login_screen_fields_are_served(
        self, aiohttp_client: Any, app: web.Application
    ) -> None:
        client = await aiohttp_client(app)
        resp = await client.get("/config.toml")
        assert resp.status == 200
        assert resp.headers["Cache-Control"] == "no-store"
        config = tomli.loads(await resp.text())
        assert set(config) == {"general"}
        assert set(config["general"]) == LOGIN_SCREEN_FIELDS
        assert config["general"]["ssoRealmName"] == "corp"

    async def test_after_login_the_whole_config_is_served(
        self, aiohttp_client: Any, app: web.Application
    ) -> None:
        client = await aiohttp_client(app)
        before_login = tomli.loads(await (await client.get("/config.toml")).text())
        await client.post("/login")
        resp = await client.get("/config.toml")
        assert resp.status == 200
        config = tomli.loads(await resp.text())
        assert set(before_login["general"]) < set(config["general"])
        assert config["general"]["hideAgents"] is False
        assert {"resources", "environments", "menu", "plugin", "wsproxy", "pipeline"} <= set(config)
        assert config["menu"]["blocklist"] == "agent"


_VERSION_JSON = '{ "package": "26.10.0", "buildNumber": "100" }'


class TestVersionJsonHandler:
    @pytest.fixture
    def app_serving_version_json(self, tmp_path: Path) -> web.Application:
        (tmp_path / "version.json").write_text(_VERSION_JSON)
        app = web.Application()
        setup_session(app, SimpleCookieStorage())
        app["config"] = WebServerUnifiedConfig.model_validate({
            "service": {"static-path": str(tmp_path)},
        })
        app.router.add_route("POST", "/login", _login)
        app.router.add_route("GET", "/version.json", version_json_handler)
        return app

    async def test_before_login_is_not_found(
        self, aiohttp_client: Any, app_serving_version_json: web.Application
    ) -> None:
        client = await aiohttp_client(app_serving_version_json)
        resp = await client.get("/version.json")
        assert resp.status == 404
        assert "26.10.0" not in await resp.text()

    async def test_after_login_is_served(
        self, aiohttp_client: Any, app_serving_version_json: web.Application
    ) -> None:
        client = await aiohttp_client(app_serving_version_json)
        await client.post("/login")
        resp = await client.get("/version.json")
        assert resp.status == 200
        assert await resp.text() == _VERSION_JSON

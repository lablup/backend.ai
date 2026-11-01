from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.typedefs import Handler
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.valkey_session.client import (
    LOGIN_FAIL_COUNT_KEY_PREFIX,
    ValkeySessionClient,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.dto.manager.auth.response import UpdatePasswordNoAuthResponse
from ai.backend.common.dto.manager.auth.types import (
    AuthResponse,
    AuthResponseType,
    AuthSuccessResponse,
    RequireTwoFactorAuthResponse,
    RequireTwoFactorRegistrationResponse,
    TwoFactorType,
)
from ai.backend.common.endpoint_pool.exceptions import NoHealthyEndpointError
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AccessKey, SecretKey, ValkeyTarget
from ai.backend.common.web.session import SESSION_KEY, Session
from ai.backend.web import server
from ai.backend.web.proxy import (
    _direct_acquire,
    _limit_password_attempts,
    web_handler,
    web_plugin_handler,
)
from ai.backend.web.server import login_handler, token_login_handler, update_password_no_auth
from ai.backend.web.stats import WebStats

ALLOWED_FAIL_COUNT = 3
AUTH_TOKEN_NAME = "sToken"
AUTH_SUCCESS = AuthSuccessResponse(
    response_type=AuthResponseType.SUCCESS,
    access_key=AccessKey("AKIATEST"),
    secret_key=SecretKey("secret"),
    role=UserRole.USER,
    status="active",
    session_token="session-token",
    user_id=UserID(uuid.uuid4()),
)

ClientFactory = Callable[[AsyncMock], Awaitable[Any]]


def _api_error(status: int) -> BackendAPIError:
    return BackendAPIError(
        status,
        "Rejected",
        {"type": "https://api.backend.ai/probs/rejected", "title": "Rejected", "msg": "rejected"},
    )


@web.middleware
async def _session_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    request[SESSION_KEY] = Session(None, data=None, new=True)
    return await handler(request)


@pytest.fixture
def valkey_target(redis_container: tuple[str, HostPortPairModel]) -> ValkeyTarget:
    return ValkeyTarget(addr=redis_container[1].address)


@pytest.fixture
async def session_client(valkey_target: ValkeyTarget) -> AsyncIterator[ValkeySessionClient]:
    client = await ValkeySessionClient.create(
        valkey_target,
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="test.web.session",
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def raw_client(valkey_target: ValkeyTarget) -> AsyncIterator[AbstractValkeyClient]:
    client = create_valkey_client(
        valkey_target=valkey_target,
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="test.web.session.raw",
    )
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
def username() -> str:
    return f"{uuid.uuid4().hex}@example.com"


@pytest.fixture
def web_client(
    aiohttp_client: Any,
    session_client: ValkeySessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> ClientFactory:
    async def build(authorize: AsyncMock) -> Any:
        monkeypatch.setattr(server, "_authorize_via_anonymous_session", authorize)

        @asynccontextmanager
        async def acquire() -> AsyncIterator[MagicMock]:
            yield MagicMock()

        manager_pool = MagicMock()
        manager_pool.acquire = acquire
        config = MagicMock()
        config.api.auth_token_name = AUTH_TOKEN_NAME
        config.session.login_allowed_fail_count = ALLOWED_FAIL_COUNT
        config.session.login_block_time = 600
        app = web.Application(middlewares=[_session_middleware])
        app["config"] = config
        app["stats"] = MagicMock()
        app["manager_pool"] = manager_pool
        app["redis"] = session_client
        app.router.add_route("POST", "/server/login", login_handler)
        app.router.add_route("POST", "/server/token-login", token_login_handler)
        return await aiohttp_client(app)

    return build


async def _fail_count(raw_client: AbstractValkeyClient, username: str) -> int:
    async with raw_client.client() as conn:
        value = await conn.get(f"{LOGIN_FAIL_COUNT_KEY_PREFIX}{username}")
    return int(value) if value is not None else 0


def _login_body(username: str, **extra: Any) -> Mapping[str, Any]:
    return {"username": username, "password": "guess", **extra}


class TestLoginFailCount:
    async def test_unauthorized_attempts_are_counted_then_blocked(
        self, web_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        authorize = AsyncMock(side_effect=_api_error(401))
        client = await web_client(authorize)

        for _ in range(ALLOWED_FAIL_COUNT):
            resp = await client.post("/server/login", json=_login_body(username))
            assert resp.status == 401
        assert await _fail_count(raw_client, username) == ALLOWED_FAIL_COUNT

        resp = await client.post("/server/login", json=_login_body(username))

        assert resp.status == 429
        assert authorize.await_count == ALLOWED_FAIL_COUNT

    async def test_success_clears_the_count(
        self, web_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        client = await web_client(AsyncMock(side_effect=[_api_error(401), AUTH_SUCCESS]))

        await client.post("/server/login", json=_login_body(username))
        assert await _fail_count(raw_client, username) == 1

        resp = await client.post("/server/login", json=_login_body(username))

        assert resp.status == 200
        assert await _fail_count(raw_client, username) == 0

    @pytest.mark.parametrize(
        "outcome",
        [
            RequireTwoFactorAuthResponse(
                response_type=AuthResponseType.REQUIRE_TWO_FACTOR_AUTH,
                type=TwoFactorType.TOTP,
            ),
            RequireTwoFactorRegistrationResponse(
                response_type=AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION,
                type=TwoFactorType.TOTP,
                token="token",
            ),
            _api_error(400),
            _api_error(409),
            _api_error(500),
            BackendClientError("unreachable"),
        ],
        ids=["2fa-auth", "2fa-registration", "400", "409", "500", "client-error"],
    )
    async def test_other_outcomes_do_not_change_the_count(
        self,
        web_client: ClientFactory,
        raw_client: AbstractValkeyClient,
        username: str,
        outcome: Any,
    ) -> None:
        client = await web_client(AsyncMock(side_effect=[_api_error(401), outcome]))
        await client.post("/server/login", json=_login_body(username))

        await client.post("/server/login", json=_login_body(username))

        assert await _fail_count(raw_client, username) == 1

    @pytest.mark.parametrize(
        ("outcome", "expected_status"),
        [
            (NoHealthyEndpointError(), 503),
            (AuthResponse(response_type=AuthResponseType.SUCCESS), 500),
        ],
        ids=["no-healthy-endpoint", "unexpected-auth-response"],
    )
    async def test_server_side_errors_release_the_reservation(
        self,
        web_client: ClientFactory,
        raw_client: AbstractValkeyClient,
        username: str,
        outcome: Any,
        expected_status: int,
    ) -> None:
        client = await web_client(AsyncMock(side_effect=[_api_error(401), outcome]))
        await client.post("/server/login", json=_login_body(username))

        resp = await client.post("/server/login", json=_login_body(username))

        assert resp.status == expected_status
        assert await _fail_count(raw_client, username) == 1

    async def test_changing_domain_shares_the_count(
        self, web_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        client = await web_client(AsyncMock(side_effect=_api_error(401)))

        await client.post("/server/login", json=_login_body(username, domain="default"))
        await client.post("/server/login", json=_login_body(username, domain="other"))

        assert await _fail_count(raw_client, username) == 2

    async def test_concurrent_failures_stop_at_the_limit(
        self, web_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        async def fail(*args: Any, **kwargs: Any) -> None:
            await asyncio.sleep(0.05)
            raise _api_error(401)

        authorize = AsyncMock(side_effect=fail)
        client = await web_client(authorize)

        responses = await asyncio.gather(*[
            client.post("/server/login", json=_login_body(username))
            for _ in range(ALLOWED_FAIL_COUNT * 4)
        ])

        statuses = [resp.status for resp in responses]
        assert statuses.count(401) == ALLOWED_FAIL_COUNT
        assert statuses.count(429) == ALLOWED_FAIL_COUNT * 3
        assert authorize.await_count == ALLOWED_FAIL_COUNT
        assert await _fail_count(raw_client, username) == ALLOWED_FAIL_COUNT


class TestTokenLoginBody:
    async def test_username_and_password_in_body_do_not_reach_authorize(
        self, web_client: ClientFactory
    ) -> None:
        authorize = AsyncMock(return_value=AUTH_SUCCESS)
        client = await web_client(authorize)

        resp = await client.post(
            "/server/token-login",
            json={
                AUTH_TOKEN_NAME: "token",
                "username": "user@example.com",
                "password": "guess",
                "otp": "123456",
                "force": True,
                "date": "2026-11-02T00:00:00Z",
                "endpoint": "https://example.com",
                "api_version": "v9",
                "app": "jupyter",
            },
        )

        assert resp.status == 200
        assert authorize.await_args is not None
        kwargs = authorize.await_args.kwargs
        assert kwargs["username"] == "fake-email"
        assert kwargs["password"] == "fake-pwd"
        assert kwargs["extra_args"] == {
            AUTH_TOKEN_NAME: "token",
            "otp": "123456",
            "force": True,
            "date": "2026-11-02T00:00:00Z",
            "endpoint": "https://example.com",
            "api_version": "v9",
            "app": "jupyter",
        }

    async def test_password_without_a_token_is_rejected(self, web_client: ClientFactory) -> None:
        authorize = AsyncMock(return_value=AUTH_SUCCESS)
        client = await web_client(authorize)

        resp = await client.post(
            "/server/token-login",
            json={"username": "user@example.com", "password": "guess"},
        )

        assert resp.status == 400
        authorize.assert_not_awaited()


def _password_update_body(username: str) -> Mapping[str, Any]:
    return {"username": username, "current_password": "guess", "new_password": "new-password"}


class TestUpdatePasswordNoAuthCount:
    @pytest.fixture
    def password_client(
        self,
        aiohttp_client: Any,
        session_client: ValkeySessionClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> ClientFactory:
        async def build(update_password: AsyncMock) -> Any:
            monkeypatch.setattr(
                server, "_authorize_via_anonymous_session", AsyncMock(side_effect=_api_error(401))
            )
            acquired = MagicMock()

            @asynccontextmanager
            async def acquire() -> AsyncIterator[MagicMock]:
                yield acquired

            manager_pool = MagicMock()
            manager_pool.acquire = acquire
            registry = MagicMock()
            registry.auth.update_password_no_auth = update_password
            config = MagicMock()
            config.session.login_allowed_fail_count = ALLOWED_FAIL_COUNT
            config.session.login_block_time = 600
            app = web.Application(middlewares=[_session_middleware])
            app["config"] = config
            app["stats"] = MagicMock()
            app["manager_pool"] = manager_pool
            app["redis"] = session_client
            app["no_auth_client_registries"] = {acquired.endpoint: registry}
            app.router.add_route("POST", "/server/login", login_handler)
            app.router.add_route("POST", "/server/update-password-no-auth", update_password_no_auth)
            return await aiohttp_client(app)

        return build

    async def test_unauthorized_attempts_are_counted_then_blocked(
        self, password_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        update_password = AsyncMock(side_effect=_api_error(401))
        client = await password_client(update_password)
        body = _password_update_body(username)

        for _ in range(ALLOWED_FAIL_COUNT):
            resp = await client.post("/server/update-password-no-auth", json=body)
            assert resp.status == 401
        assert await _fail_count(raw_client, username) == ALLOWED_FAIL_COUNT

        resp = await client.post("/server/update-password-no-auth", json=body)

        assert resp.status == 429
        assert update_password.await_count == ALLOWED_FAIL_COUNT

    async def test_success_clears_the_count(
        self, password_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        success = UpdatePasswordNoAuthResponse(password_changed_at="2026-09-29T00:00:00+00:00")
        client = await password_client(AsyncMock(side_effect=[_api_error(401), success]))
        body = _password_update_body(username)

        await client.post("/server/update-password-no-auth", json=body)
        assert await _fail_count(raw_client, username) == 1

        resp = await client.post("/server/update-password-no-auth", json=body)

        assert resp.status == 200
        assert await _fail_count(raw_client, username) == 0

    @pytest.mark.parametrize(
        "outcome",
        [_api_error(400), _api_error(500), BackendClientError("unreachable")],
        ids=["400", "500", "client-error"],
    )
    async def test_other_outcomes_do_not_change_the_count(
        self,
        password_client: ClientFactory,
        raw_client: AbstractValkeyClient,
        username: str,
        outcome: Exception,
    ) -> None:
        client = await password_client(AsyncMock(side_effect=[_api_error(401), outcome]))
        body = _password_update_body(username)
        await client.post("/server/update-password-no-auth", json=body)

        await client.post("/server/update-password-no-auth", json=body)

        assert await _fail_count(raw_client, username) == 1

    async def test_shares_the_count_with_login(
        self, password_client: ClientFactory, raw_client: AbstractValkeyClient, username: str
    ) -> None:
        update_password = AsyncMock(side_effect=_api_error(401))
        client = await password_client(update_password)

        for _ in range(ALLOWED_FAIL_COUNT):
            await client.post("/server/login", json=_login_body(username))

        resp = await client.post(
            "/server/update-password-no-auth", json=_password_update_body(username)
        )

        assert resp.status == 429
        update_password.assert_not_awaited()


@dataclass
class _Manager:
    url: str = ""
    statuses: list[int] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    bodies: list[bytes] = field(default_factory=list)


@pytest.fixture
async def manager(aiohttp_server: Any) -> _Manager:
    manager = _Manager()

    async def handler(request: web.Request) -> web.Response:
        manager.paths.append(request.path)
        manager.bodies.append(await request.read())
        await asyncio.sleep(0.01)
        status = manager.statuses.pop(0) if manager.statuses else 401
        return web.json_response({"title": "response", "type": "about:blank"}, status=status)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    server_ = await aiohttp_server(app)
    manager.url = str(server_.make_url("/"))
    return manager


@pytest.fixture
async def client_pool() -> AsyncIterator[ClientPool]:
    pool = ClientPool(
        partial(tcp_client_session_factory, ssl=False, limit=20, limit_per_host=20),
        cleanup_interval_seconds=100,
    )
    try:
        yield pool
    finally:
        await pool.close()


DECRYPTED_HEADER = "X-Test-Decrypted-Body"


@web.middleware
async def _decrypted_payload_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    decrypted = request.headers.get(DECRYPTED_HEADER)
    request["payload"] = decrypted.encode() if decrypted is not None else None
    return await handler(request)


@pytest.fixture
async def proxy_client(
    aiohttp_client: Any,
    session_client: ValkeySessionClient,
    client_pool: ClientPool,
    manager: _Manager,
) -> Any:
    endpoint_pool = MagicMock()
    endpoint_pool.acquire = lambda *, exclude=(): _direct_acquire(manager.url)
    config = MagicMock(
        api=MagicMock(domain="default", ssl_verify=False),
        service=MagicMock(enable_signup=True),
    )
    config.session.login_allowed_fail_count = ALLOWED_FAIL_COUNT
    config.session.login_block_time = 600
    app = web.Application(middlewares=[_session_middleware, _decrypted_payload_middleware])
    app["config"] = config
    app["client_pool"] = client_pool
    app["stats"] = WebStats()
    app["manager_pool"] = endpoint_pool
    app["redis"] = session_client
    app.router.add_route("POST", "/server/login", login_handler)
    app.router.add_route(
        "POST",
        "/func/{path:cloud/.*$}",
        partial(web_plugin_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    app.router.add_route(
        "*",
        "/session-required/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=False),
    )
    # The catch-all is signed-in in production; anonymous here spares the signature setup.
    app.router.add_route(
        "*",
        "/func/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    return await aiohttp_client(app)


def _raw_url(path: str) -> URL:
    return URL(path, encoded=True)


PASSWORD_CHECK_ROUTES = [
    "/func/auth/authorize",
    "/func/auth/update-password-no-auth",
    "/func/auth/x/%2E%2E/authorize",
    "/func/cloud/%2E%2E/auth/authorize",
]


@pytest.mark.parametrize("route", PASSWORD_CHECK_ROUTES)
class TestProxiedPasswordChecks:
    async def test_unauthorized_attempts_are_counted_then_blocked(
        self,
        proxy_client: Any,
        manager: _Manager,
        raw_client: AbstractValkeyClient,
        username: str,
        route: str,
    ) -> None:
        for _ in range(ALLOWED_FAIL_COUNT):
            resp = await proxy_client.post(_raw_url(route), json=_login_body(username))
            assert resp.status == 401
        assert await _fail_count(raw_client, username) == ALLOWED_FAIL_COUNT

        resp = await proxy_client.post(_raw_url(route), json=_login_body(username))

        assert resp.status == 429
        assert len(manager.paths) == ALLOWED_FAIL_COUNT

    @pytest.mark.parametrize("status", [200, 400, 500])
    async def test_other_statuses_do_not_change_the_count(
        self,
        proxy_client: Any,
        manager: _Manager,
        raw_client: AbstractValkeyClient,
        username: str,
        route: str,
        status: int,
    ) -> None:
        manager.statuses = [401, status]
        await proxy_client.post(_raw_url(route), json=_login_body(username))

        resp = await proxy_client.post(_raw_url(route), json=_login_body(username))

        assert resp.status == status
        assert await _fail_count(raw_client, username) == 1

    async def test_body_reaches_the_manager_unchanged(
        self, proxy_client: Any, manager: _Manager, username: str, route: str
    ) -> None:
        body = f'{{"username":  "{username}", "password": "guess"}}'.encode()

        await proxy_client.post(
            _raw_url(route), data=body, headers={"Content-Type": "application/json"}
        )

        assert manager.bodies == [body]

    @pytest.mark.parametrize(
        ("body", "content_type"),
        [
            (b"not json", "application/json"),
            (b'["username"]', "application/json"),
            (b'{"password": "guess"}', "application/json"),
            (b'{"username": 1}', "application/json"),
            (b'{"username": "user"}', "application/json; charset=utf-7"),
        ],
        ids=["not-json", "not-object", "no-username", "non-string", "other-charset"],
    )
    async def test_unreadable_body_is_rejected_without_forwarding(
        self, proxy_client: Any, manager: _Manager, route: str, body: bytes, content_type: str
    ) -> None:
        resp = await proxy_client.post(
            _raw_url(route), data=body, headers={"Content-Type": content_type}
        )

        assert resp.status == 400
        assert manager.paths == []

    async def test_concurrent_failures_stop_at_the_limit(
        self,
        proxy_client: Any,
        manager: _Manager,
        raw_client: AbstractValkeyClient,
        username: str,
        route: str,
    ) -> None:
        responses = await asyncio.gather(*[
            proxy_client.post(_raw_url(route), json=_login_body(username))
            for _ in range(ALLOWED_FAIL_COUNT * 4)
        ])

        statuses = [resp.status for resp in responses]
        assert statuses.count(401) == ALLOWED_FAIL_COUNT
        assert statuses.count(429) == ALLOWED_FAIL_COUNT * 3
        assert len(manager.paths) == ALLOWED_FAIL_COUNT
        assert await _fail_count(raw_client, username) == ALLOWED_FAIL_COUNT


class TestProxiedPasswordCheckBoundaries:
    async def test_shares_the_count_with_login(
        self,
        proxy_client: Any,
        username: str,
    ) -> None:
        for _ in range(ALLOWED_FAIL_COUNT):
            await proxy_client.post("/func/auth/authorize", json=_login_body(username))

        resp = await proxy_client.post("/server/login", json=_login_body(username))

        assert resp.status == 429

    async def test_session_rejection_does_not_change_the_count(
        self,
        proxy_client: Any,
        manager: _Manager,
        raw_client: AbstractValkeyClient,
        username: str,
    ) -> None:
        resp = await proxy_client.post(
            "/session-required/auth/authorize", json=_login_body(username)
        )

        assert resp.status == 401
        assert manager.paths == []
        assert await _fail_count(raw_client, username) == 0

    async def test_decrypted_payload_is_counted_and_forwarded(
        self,
        proxy_client: Any,
        manager: _Manager,
        raw_client: AbstractValkeyClient,
        username: str,
    ) -> None:
        decrypted = f'{{"username": "{username}", "password": "guess"}}'

        resp = await proxy_client.post(
            "/func/auth/authorize",
            data=b"encrypted",
            headers={
                "Content-Type": "application/json",
                "X-BackendAI-Encoded": "true",
                DECRYPTED_HEADER: decrypted,
            },
        )

        assert resp.status == 401
        assert manager.bodies == [decrypted.encode()]
        assert await _fail_count(raw_client, username) == 1

    @pytest.mark.parametrize(
        ("method", "route"),
        [("POST", "/func/auth/role"), ("GET", "/func/auth/authorize")],
    )
    async def test_other_requests_are_not_counted(
        self,
        proxy_client: Any,
        raw_client: AbstractValkeyClient,
        username: str,
        method: str,
        route: str,
    ) -> None:
        resp = await proxy_client.request(method, route, json=_login_body(username))

        assert resp.status == 401
        assert await _fail_count(raw_client, username) == 0

    async def test_closed_connection_keeps_the_reservation(self, username: str) -> None:
        request = MagicMock(spec=web.Request)
        request.get.return_value = None
        request.read = AsyncMock(return_value=f'{{"username": "{username}"}}'.encode())
        request.charset = None
        request.transport = MagicMock(is_closing=MagicMock(return_value=True))
        redis = AsyncMock()
        redis.reserve_login_attempt.return_value = True
        request.app = {"redis": redis, "config": MagicMock()}

        with pytest.raises(ConnectionResetError):
            await _limit_password_attempts(request, AsyncMock(side_effect=ConnectionResetError()))

        redis.release_login_attempt.assert_not_awaited()

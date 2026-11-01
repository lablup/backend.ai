from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.valkey_session.client import (
    LOGIN_FAIL_COUNT_KEY_PREFIX,
    ValkeySessionClient,
)
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.dto.manager.auth.types import (
    AuthSuccessResponse,
    RequireTwoFactorAuthResponse,
    RequireTwoFactorRegistrationResponse,
    TwoFactorType,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget
from ai.backend.common.web.session import SESSION_KEY, Session
from ai.backend.web import server
from ai.backend.web.server import login_handler, token_login_handler

ALLOWED_FAIL_COUNT = 3
AUTH_TOKEN_NAME = "sToken"
AUTH_SUCCESS = AuthSuccessResponse(
    access_key="AKIATEST",
    secret_key="secret",
    role="user",
    status="active",
    session_token="session-token",
    user_id=uuid.uuid4(),
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
            RequireTwoFactorAuthResponse(type=TwoFactorType.TOTP),
            RequireTwoFactorRegistrationResponse(type=TwoFactorType.TOTP, token="token"),
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

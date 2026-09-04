from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from pytest_mock import MockerFixture

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.web import ratelimit
from ai.backend.web.ratelimit import manager_proxy_rate_limited

_USER_ID = UserID(uuid.UUID("12345678-1234-5678-1234-567812345678"))
_RATE_LIMIT = 1000
_RESET = 500
_AUTHENTICATED_SESSION = {"authenticated": True, "token": {"user_id": str(_USER_ID)}}


@pytest.fixture
def mock_valkey_rate_limit_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeyRateLimitClient)
    client.get_state.return_value = RateLimitState(count=0, limit=_RATE_LIMIT, reset=_RESET)
    return client


@pytest.fixture
def proxied_request(mock_valkey_rate_limit_client: AsyncMock) -> web.Request:
    return make_mocked_request(
        "GET", "/func/session", app={"valkey_rate_limit": mock_valkey_rate_limit_client}
    )


@pytest.fixture
def handler_response() -> web.Response:
    return web.Response(text="ok")


@pytest.fixture
def handler(handler_response: web.Response) -> AsyncMock:
    return AsyncMock(return_value=handler_response)


@dataclass(frozen=True)
class _PassThroughCase:
    id: str
    session: dict[str, Any]
    state: RateLimitState | None = RateLimitState(count=0, limit=_RATE_LIMIT, reset=_RESET)


@pytest.mark.parametrize(
    "case",
    [
        # No login session: nothing to count against, the manager rejects it anyway.
        _PassThroughCase(
            id="unauthenticated",
            session={},
        ),
        # Session created before login stored the user id: no counter key, so exempt.
        _PassThroughCase(
            id="session-stored-before-user-id",
            session={"authenticated": True, "token": {"access_key": "AKTEST"}},
        ),
        # No window open for the user: proxied, the manager opens one.
        _PassThroughCase(
            id="no-open-window",
            session=_AUTHENTICATED_SESSION,
            state=None,
        ),
        # Window without a limit: proxied unlimited.
        _PassThroughCase(
            id="window-without-limit",
            session=_AUTHENTICATED_SESSION,
            state=RateLimitState(count=5000, limit=None, reset=_RESET),
        ),
    ],
    ids=lambda case: case.id,
)
async def test_pass_through_without_rate_limiting(
    case: _PassThroughCase,
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    proxied_request: web.Request,
    handler: AsyncMock,
    handler_response: web.Response,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=case.session))
    mock_valkey_rate_limit_client.get_state.return_value = case.state

    response = await manager_proxy_rate_limited(handler)(proxied_request)

    assert response is handler_response
    handler.assert_awaited_once_with(proxied_request)
    assert "X-RateLimit-Limit" not in response.headers


@dataclass(frozen=True)
class _LimitCase:
    id: str
    count: int
    expected_status: int
    expected_content_type: str
    expected_handler_awaits: int


@pytest.mark.parametrize(
    "case",
    [
        # Nothing counted yet in the window: proxied, the manager counts it.
        _LimitCase(
            id="count-below-limit-is-proxied",
            count=0,
            expected_status=200,
            expected_content_type="text/plain",
            expected_handler_awaits=1,
        ),
        # One slot left: still proxied, the manager takes the last slot.
        _LimitCase(
            id="count-one-below-limit-is-still-proxied",
            count=_RATE_LIMIT - 1,
            expected_status=200,
            expected_content_type="text/plain",
            expected_handler_awaits=1,
        ),
        # Limit already reached: 429 from the web server, the handler never runs.
        _LimitCase(
            id="count-at-limit-gets-429-without-reaching-the-handler",
            count=_RATE_LIMIT,
            expected_status=429,
            expected_content_type="application/problem+json",
            expected_handler_awaits=0,
        ),
    ],
    ids=lambda case: case.id,
)
async def test_gates_on_the_user_count(
    case: _LimitCase,
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    proxied_request: web.Request,
    handler: AsyncMock,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=_AUTHENTICATED_SESSION))
    mock_valkey_rate_limit_client.get_state.return_value = RateLimitState(
        count=case.count, limit=_RATE_LIMIT, reset=_RESET
    )

    response = await manager_proxy_rate_limited(handler)(proxied_request)

    assert response.status == case.expected_status
    assert response.content_type == case.expected_content_type
    assert handler.await_count == case.expected_handler_awaits
    mock_valkey_rate_limit_client.get_state.assert_awaited_once_with(_USER_ID)
    mock_valkey_rate_limit_client.consume.assert_not_called()


async def test_429_carries_the_rate_limit_headers(
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    proxied_request: web.Request,
    handler: AsyncMock,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=_AUTHENTICATED_SESSION))
    mock_valkey_rate_limit_client.get_state.return_value = RateLimitState(
        count=_RATE_LIMIT, limit=_RATE_LIMIT, reset=_RESET
    )

    response = await manager_proxy_rate_limited(handler)(proxied_request)

    assert response.headers["X-RateLimit-Limit"] == str(_RATE_LIMIT)
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Reset"] == str(_RESET)
    assert response.headers["X-RateLimit-Window"] == str(ratelimit._RATELIMIT_WINDOW)

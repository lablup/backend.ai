from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from pytest_mock import MockerFixture

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.identifier.user import UserID
from ai.backend.web import ratelimit
from ai.backend.web.ratelimit import rate_limit_middleware

_USER_ID = UserID(uuid.UUID("12345678-1234-5678-1234-567812345678"))
_RATE_LIMIT = 1000
_AUTHENTICATED_SESSION = {"authenticated": True, "token": {"user_id": str(_USER_ID)}}


@pytest.fixture
def mock_valkey_rate_limit_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeyRateLimitClient)
    client.get_user_rate_limit.return_value = _RATE_LIMIT
    client.execute_rate_limit_logic.return_value = 1
    return client


@pytest.fixture
def handler_response() -> web.Response:
    return web.Response(text="ok")


@pytest.fixture
def handler(handler_response: web.Response) -> AsyncMock:
    return AsyncMock(return_value=handler_response)


@dataclass(frozen=True)
class _PassThroughCase:
    id: str
    path: str
    session: dict[str, Any]
    published_rate_limit: int | None = _RATE_LIMIT


@pytest.mark.parametrize(
    "case",
    [
        _PassThroughCase(
            id="non-proxied-path",
            path="/server/login",
            session=_AUTHENTICATED_SESSION,
        ),
        _PassThroughCase(
            id="unauthenticated",
            path="/func/session",
            session={},
        ),
        _PassThroughCase(
            id="session-stored-before-user-id",
            path="/func/session",
            session={"authenticated": True, "token": {"access_key": "AKTEST"}},
        ),
        _PassThroughCase(
            id="no-published-rate-limit",
            path="/func/session",
            session=_AUTHENTICATED_SESSION,
            published_rate_limit=None,
        ),
    ],
    ids=lambda case: case.id,
)
async def test_pass_through_without_rate_limiting(
    case: _PassThroughCase,
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    handler: AsyncMock,
    handler_response: web.Response,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=case.session))
    mock_valkey_rate_limit_client.get_user_rate_limit.return_value = case.published_rate_limit
    request = make_mocked_request(
        "GET", case.path, app={"valkey_rate_limit": mock_valkey_rate_limit_client}
    )

    response = await rate_limit_middleware(request, handler)

    assert response is handler_response
    handler.assert_awaited_once_with(request)
    mock_valkey_rate_limit_client.execute_rate_limit_logic.assert_not_called()
    assert "X-RateLimit-Limit" not in response.headers


async def test_counts_request_per_user_and_sets_headers(
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    handler: AsyncMock,
    handler_response: web.Response,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=_AUTHENTICATED_SESSION))
    request = make_mocked_request(
        "GET", "/func/session", app={"valkey_rate_limit": mock_valkey_rate_limit_client}
    )

    response = await rate_limit_middleware(request, handler)

    assert response is handler_response
    mock_valkey_rate_limit_client.get_user_rate_limit.assert_awaited_once_with(_USER_ID)
    mock_valkey_rate_limit_client.execute_rate_limit_logic.assert_awaited_once_with(
        user_id=_USER_ID,
        window=ratelimit._rlim_window,
    )
    assert response.headers["X-RateLimit-Limit"] == str(_RATE_LIMIT)
    assert response.headers["X-RateLimit-Remaining"] == str(_RATE_LIMIT - 1)
    assert response.headers["X-RateLimit-Window"] == str(ratelimit._rlim_window)


async def test_rejects_over_limit_request_with_429(
    mocker: MockerFixture,
    mock_valkey_rate_limit_client: AsyncMock,
    handler: AsyncMock,
) -> None:
    mocker.patch.object(ratelimit, "get_session", AsyncMock(return_value=_AUTHENTICATED_SESSION))
    mock_valkey_rate_limit_client.execute_rate_limit_logic.return_value = _RATE_LIMIT + 1
    request = make_mocked_request(
        "GET", "/func/session", app={"valkey_rate_limit": mock_valkey_rate_limit_client}
    )

    response = await rate_limit_middleware(request, handler)

    handler.assert_not_called()
    assert isinstance(response, web.HTTPTooManyRequests)
    assert response.content_type == "application/problem+json"
    assert response.headers["X-RateLimit-Limit"] == str(_RATE_LIMIT)
    assert response.headers["X-RateLimit-Remaining"] == "0"

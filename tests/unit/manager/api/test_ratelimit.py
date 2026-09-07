from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.contexts.client_ip import with_client_ip
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.web.reserved_response_headers import apply_reserved_response_headers
from ai.backend.manager.api.rest.ratelimit.handler import (
    _ANONYMOUS_RATELIMIT,
    _RATELIMIT_WINDOW_SECONDS,
    make_rlim_middleware,
)
from ai.backend.manager.errors.api import RateLimitExceeded

_USER_ID = UserID(uuid.UUID("12345678-1234-5678-1234-567812345678"))
_CLIENT_IP = "10.0.0.1"
_RATE_LIMIT = 30000
_RESET_AFTER_SECONDS = 500


@dataclass(frozen=True)
class Caller:
    """A caller as the middleware meets it: the request it arrives on, and the client
    call that opens the window its identity keys."""

    request: web.Request
    consumer: AsyncMock


@dataclass(frozen=True)
class RateLimitSuccessCase:
    """A window state the request is served under, and the quota headers it reports."""

    description: str
    limit: int
    count: int
    expected_remaining: str


@dataclass(frozen=True)
class RateLimitExceedCase:
    """A window state the request is refused under, and the limit the 429 reports."""

    description: str
    limit: int
    count: int


class TestRlimMiddleware:
    @pytest.fixture
    def mock_valkey_client(self) -> MagicMock:
        """Mock ValkeyRateLimitClient."""
        client = MagicMock(spec=ValkeyRateLimitClient)
        client.consume_user_rate_limit = AsyncMock()
        client.consume_ip_rate_limit = AsyncMock()
        return client

    @pytest.fixture
    def middleware(self, mock_valkey_client: MagicMock) -> Any:
        """Create the closure-based rate limit middleware."""
        return make_rlim_middleware(mock_valkey_client)

    @pytest.fixture
    def mock_handler(self) -> AsyncMock:
        """Mock downstream handler that returns a response."""
        handler = AsyncMock()
        handler.return_value = web.Response(status=200, text="OK")
        return handler

    @pytest.fixture
    def anonymous_caller(self, mock_valkey_client: MagicMock) -> Iterator[Caller]:
        """An unauthenticated caller, whose address the request context carries."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = False
        request["user"] = None
        with with_client_ip(_CLIENT_IP):
            yield Caller(request=request, consumer=mock_valkey_client.consume_ip_rate_limit)

    @pytest.fixture
    def authorized_caller(self, mock_valkey_client: MagicMock) -> Caller:
        """A caller the auth middleware resolved, carrying the rate limit it injected."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = True
        request["user"] = {"uuid": _USER_ID, "rate_limit": _RATE_LIMIT}
        return Caller(request=request, consumer=mock_valkey_client.consume_user_rate_limit)

    @pytest.fixture
    def caller(self, request: pytest.FixtureRequest) -> Caller:
        """The caller named by the parametrized fixture."""
        caller: Caller = request.getfixturevalue(request.param)
        return caller

    @pytest.mark.parametrize(
        ("caller", "expected_limit"),
        [
            ("anonymous_caller", _ANONYMOUS_RATELIMIT),
            ("authorized_caller", _RATE_LIMIT),
        ],
        indirect=["caller"],
    )
    async def test_a_query_is_judged_by_its_own_window(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        caller: Caller,
        expected_limit: int,
        mock_handler: AsyncMock,
    ) -> None:
        """The two windows stand apart, so the limit reported says which one governed."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit.return_value = RateLimitState(
            count=1, limit=_RATE_LIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
        )
        mock_valkey_client.consume_ip_rate_limit.return_value = RateLimitState(
            count=1, limit=_ANONYMOUS_RATELIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act
        response = await middleware(caller.request, mock_handler)
        await apply_reserved_response_headers(caller.request, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == str(expected_limit)

    @pytest.mark.parametrize("caller", ["anonymous_caller", "authorized_caller"], indirect=True)
    @pytest.mark.parametrize(
        "case",
        [
            RateLimitSuccessCase(
                description="within limit",
                limit=_RATE_LIMIT,
                count=10,
                expected_remaining="29990",
            ),
            RateLimitSuccessCase(
                description="exactly at limit",
                limit=_RATE_LIMIT,
                count=_RATE_LIMIT,
                expected_remaining="0",
            ),
            RateLimitSuccessCase(
                description="zero limit before any request lands",
                limit=0,
                count=0,
                expected_remaining="0",
            ),
            RateLimitSuccessCase(
                description="the limit the window holds, not the one asked for",
                limit=100,
                count=10,
                expected_remaining="90",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_the_quota_headers_report_the_window(
        self,
        middleware: Any,
        caller: Caller,
        mock_handler: AsyncMock,
        case: RateLimitSuccessCase,
    ) -> None:
        """The headers report the window as it stands, whatever limit the request carried."""
        # Arrange
        caller.consumer.return_value = RateLimitState(
            count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act
        response = await middleware(caller.request, mock_handler)
        await apply_reserved_response_headers(caller.request, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == case.expected_remaining
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_called_once_with(caller.request)

    @pytest.mark.parametrize("caller", ["anonymous_caller", "authorized_caller"], indirect=True)
    @pytest.mark.parametrize(
        "case",
        [
            RateLimitExceedCase(
                description="exceeds by 1", limit=_RATE_LIMIT, count=_RATE_LIMIT + 1
            ),
            RateLimitExceedCase(description="far exceeds limit", limit=_RATE_LIMIT, count=50000),
            RateLimitExceedCase(description="zero limit always exceeds", limit=0, count=1),
        ],
        ids=lambda case: case.description,
    )
    async def test_a_query_past_its_window_is_refused(
        self,
        middleware: Any,
        caller: Caller,
        mock_handler: AsyncMock,
        case: RateLimitExceedCase,
    ) -> None:
        """A request past the window it was counted in gets 429 and never reaches the handler."""
        # Arrange
        caller.consumer.return_value = RateLimitState(
            count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await middleware(caller.request, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(caller.request, response)
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_not_called()

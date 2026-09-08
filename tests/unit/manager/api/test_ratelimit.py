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
class RateLimitSuccessCase:
    """A window the request stays within, and the quota headers it reports."""

    limit: int
    count: int
    expected_remaining: str
    description: str


class TestRlimMiddleware:
    @pytest.fixture
    def mock_valkey_client(self) -> MagicMock:
        """Mock ValkeyRateLimitClient."""
        client = MagicMock(spec=ValkeyRateLimitClient)
        client.consume_user_rlim_window = AsyncMock()
        client.consume_ip_rlim_window = AsyncMock()
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
    def mock_request_anonymous(self) -> Iterator[web.Request]:
        """An unauthenticated request, whose address the context carries."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = False
        request["user"] = None
        with with_client_ip(_CLIENT_IP):
            yield request

    @pytest.fixture
    def mock_request_authorized(self) -> web.Request:
        """A request carrying the user and rate limit the auth middleware resolved."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = True
        request["user"] = {"uuid": _USER_ID, "rate_limit": _RATE_LIMIT}
        return request

    @pytest.fixture
    def mock_request(self, request: pytest.FixtureRequest) -> web.Request:
        """The request named by the parametrized fixture."""
        mock_request: web.Request = request.getfixturevalue(request.param)
        return mock_request

    @pytest.mark.parametrize(
        ("mock_request", "expected_limit"),
        [
            ("mock_request_anonymous", _ANONYMOUS_RATELIMIT),
            ("mock_request_authorized", _RATE_LIMIT),
        ],
        indirect=["mock_request"],
    )
    async def test_a_query_is_judged_by_its_own_window(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request: web.Request,
        expected_limit: int,
        mock_handler: AsyncMock,
    ) -> None:
        """The two windows stand apart, so the limit reported says which one governed."""
        # Arrange
        mock_valkey_client.consume_ip_rlim_window.return_value = RateLimitState(
            count=1, limit=_ANONYMOUS_RATELIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
        )
        mock_valkey_client.consume_user_rlim_window.return_value = RateLimitState(
            count=1, limit=_RATE_LIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act
        response = await middleware(mock_request, mock_handler)
        await apply_reserved_response_headers(mock_request, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == str(expected_limit)

    @pytest.mark.parametrize(
        "case",
        [
            RateLimitSuccessCase(
                limit=_RATE_LIMIT,
                count=10,
                expected_remaining="29990",
                description="within limit",
            ),
            RateLimitSuccessCase(
                limit=_RATE_LIMIT,
                count=_RATE_LIMIT,
                expected_remaining="0",
                description="exactly at limit",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_the_quota_headers_report_the_window(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        case: RateLimitSuccessCase,
    ) -> None:
        """The headers report the window as it stands, whatever limit the request carried."""
        # Arrange
        mock_valkey_client.consume_user_rlim_window.return_value = RateLimitState(
            count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act
        response = await middleware(mock_request_authorized, mock_handler)
        await apply_reserved_response_headers(mock_request_authorized, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == case.expected_remaining
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_called_once_with(mock_request_authorized)

    async def test_a_query_past_its_window_is_refused(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """One request past the limit is refused, and the quota survives the raise."""
        # Arrange
        mock_valkey_client.consume_user_rlim_window.return_value = RateLimitState(
            count=_RATE_LIMIT + 1, limit=_RATE_LIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await middleware(mock_request_authorized, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(mock_request_authorized, response)
        assert response.headers["X-RateLimit-Limit"] == str(_RATE_LIMIT)
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_not_called()

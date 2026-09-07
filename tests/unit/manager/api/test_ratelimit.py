from __future__ import annotations

import uuid
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
from ai.backend.common.exception import UnreachableError
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


@dataclass(frozen=True)
class RateLimitExceedCase:
    """A window the request runs past, and the limit the 429 reports."""

    limit: int
    count: int
    description: str


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
    def mock_request_anonymous(self) -> web.Request:
        """Mock request for anonymous user."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = False
        return request

    @pytest.fixture
    def mock_request_authorized(self) -> web.Request:
        """Mock request carrying the rate limit the auth middleware injected."""
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = True
        request["user"] = {"uuid": _USER_ID, "rate_limit": _RATE_LIMIT}
        return request

    async def test_anonymous_query_counts_against_the_client_address(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_anonymous: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """An unauthenticated request names no keypair, so its address is the window key."""
        # Arrange
        mock_valkey_client.consume_ip_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=1, limit=_ANONYMOUS_RATELIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
            )
        )

        # Act
        with with_client_ip(_CLIENT_IP):
            response = await middleware(mock_request_anonymous, mock_handler)
        await apply_reserved_response_headers(mock_request_anonymous, response)

        # Assert
        mock_valkey_client.consume_ip_rate_limit.assert_called_once_with(
            client_ip=_CLIENT_IP,
            window_seconds=_RATELIMIT_WINDOW_SECONDS,
            limit=_ANONYMOUS_RATELIMIT,
        )
        mock_valkey_client.consume_user_rate_limit.assert_not_called()
        assert response.headers["X-RateLimit-Limit"] == str(_ANONYMOUS_RATELIMIT)
        assert response.headers["X-RateLimit-Remaining"] == str(_ANONYMOUS_RATELIMIT - 1)
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_called_once_with(mock_request_anonymous)

    async def test_anonymous_query_exceeding_its_address_limit_is_refused(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_anonymous: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """The anonymous window is enforced, not merely reported."""
        # Arrange
        mock_valkey_client.consume_ip_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=_ANONYMOUS_RATELIMIT + 1,
                limit=_ANONYMOUS_RATELIMIT,
                reset_after_seconds=_RESET_AFTER_SECONDS,
            )
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded), with_client_ip(_CLIENT_IP):
            await middleware(mock_request_anonymous, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(mock_request_anonymous, response)
        assert response.headers["X-RateLimit-Limit"] == str(_ANONYMOUS_RATELIMIT)
        assert response.headers["X-RateLimit-Remaining"] == "0"
        mock_handler.assert_not_called()

    async def test_an_anonymous_query_without_a_client_address_is_refused(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_anonymous: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """No address means no window to count in, and serving uncounted is not the answer."""
        # Act & Assert
        with pytest.raises(UnreachableError):
            await middleware(mock_request_anonymous, mock_handler)
        mock_valkey_client.consume_ip_rate_limit.assert_not_called()
        mock_handler.assert_not_called()

    async def test_authorized_query_counts_against_the_injected_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """The limit the auth middleware put on the request is what opens the window."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=1, limit=_RATE_LIMIT, reset_after_seconds=_RESET_AFTER_SECONDS
            )
        )

        # Act
        await middleware(mock_request_authorized, mock_handler)

        # Assert
        mock_valkey_client.consume_user_rate_limit.assert_called_once_with(
            user_id=_USER_ID,
            window_seconds=_RATELIMIT_WINDOW_SECONDS,
            limit=_RATE_LIMIT,
        )
        mock_valkey_client.consume_ip_rate_limit.assert_not_called()

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
            RateLimitSuccessCase(
                limit=0,
                count=0,
                expected_remaining="0",
                description="zero limit before any request lands",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_authorized_query_within_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        case: RateLimitSuccessCase,
    ) -> None:
        """Authorized requests within rate limit succeed and return correct headers."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
            )
        )

        # Act
        response = await middleware(mock_request_authorized, mock_handler)
        await apply_reserved_response_headers(mock_request_authorized, response)

        # Assert headers
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == case.expected_remaining
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)

        # Handler should be called
        mock_handler.assert_called_once_with(mock_request_authorized)

    async def test_the_limit_fixed_for_the_window_outranks_the_injected_one(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """A window keeps the limit it opened with, so a later change waits for the next one."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=10, limit=100, reset_after_seconds=_RESET_AFTER_SECONDS
            )
        )

        # Act
        response = await middleware(mock_request_authorized, mock_handler)
        await apply_reserved_response_headers(mock_request_authorized, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "90"

    @pytest.mark.parametrize(
        "case",
        [
            RateLimitExceedCase(
                limit=_RATE_LIMIT,
                count=_RATE_LIMIT + 1,
                description="exceeds by 1",
            ),
            RateLimitExceedCase(
                limit=_RATE_LIMIT,
                count=50000,
                description="far exceeds limit",
            ),
            RateLimitExceedCase(
                limit=0,
                count=1,
                description="zero limit always exceeds",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_authorized_query_exceeds_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        case: RateLimitExceedCase,
    ) -> None:
        """Authorized requests exceeding rate limit raise RateLimitExceeded."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit = AsyncMock(
            return_value=RateLimitState(
                count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
            )
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await middleware(mock_request_authorized, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(mock_request_authorized, response)
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)

        # Handler should not be called when rate limit exceeded
        mock_handler.assert_not_called()

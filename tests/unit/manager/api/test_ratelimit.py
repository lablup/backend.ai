from __future__ import annotations

import uuid
from collections.abc import Mapping
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
class _Caller:
    """A caller the middleware can meet, and the window its identity opens."""

    description: str
    request_state: Mapping[str, Any]
    limit: int
    consumer: str
    other_consumer: str
    expected_kwargs: Mapping[str, Any]


@dataclass(frozen=True)
class _WithinWindowCase:
    """A window the request stays within, and the quota headers it reports."""

    description: str
    limit: int
    count: int
    expected_remaining: str


@dataclass(frozen=True)
class _PastWindowCase:
    """A window the request runs past, and the limit the 429 reports."""

    description: str
    limit: int
    count: int


_ANONYMOUS = _Caller(
    description="anonymous",
    request_state={"is_authorized": False, "user": None},
    limit=_ANONYMOUS_RATELIMIT,
    consumer="consume_ip_rate_limit",
    other_consumer="consume_user_rate_limit",
    expected_kwargs={
        "client_ip": _CLIENT_IP,
        "window_seconds": _RATELIMIT_WINDOW_SECONDS,
        "limit": _ANONYMOUS_RATELIMIT,
    },
)
_AUTHORIZED = _Caller(
    description="authorized",
    request_state={
        "is_authorized": True,
        "user": {"uuid": _USER_ID, "rate_limit": _RATE_LIMIT},
    },
    limit=_RATE_LIMIT,
    consumer="consume_user_rate_limit",
    other_consumer="consume_ip_rate_limit",
    expected_kwargs={
        "user_id": _USER_ID,
        "window_seconds": _RATELIMIT_WINDOW_SECONDS,
        "limit": _RATE_LIMIT,
    },
)


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
    def caller_request(self, caller: _Caller) -> web.Request:
        """A request carrying what the auth middleware left about its caller."""
        request = make_mocked_request("GET", "/")
        request.update(caller.request_state)
        return request

    @pytest.fixture
    def authorized_request(self) -> web.Request:
        """A request whose caller is known, for the rules that hold for any caller."""
        request = make_mocked_request("GET", "/")
        request.update(_AUTHORIZED.request_state)
        return request

    @pytest.mark.parametrize("caller", [_ANONYMOUS, _AUTHORIZED], ids=lambda c: c.description)
    async def test_the_window_a_caller_opens(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        caller: _Caller,
        caller_request: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """Which identity keys the window: the user when there is one, the address otherwise."""
        # Arrange
        state = RateLimitState(
            count=1, limit=caller.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )
        getattr(mock_valkey_client, caller.consumer).return_value = state

        # Act
        with with_client_ip(_CLIENT_IP):
            response = await middleware(caller_request, mock_handler)
        await apply_reserved_response_headers(caller_request, response)

        # Assert
        getattr(mock_valkey_client, caller.consumer).assert_called_once_with(
            **caller.expected_kwargs
        )
        getattr(mock_valkey_client, caller.other_consumer).assert_not_called()
        assert response.headers["X-RateLimit-Limit"] == str(caller.limit)
        assert response.headers["X-RateLimit-Remaining"] == str(caller.limit - 1)
        mock_handler.assert_called_once_with(caller_request)

    @pytest.mark.parametrize(
        "case",
        [
            _WithinWindowCase(
                description="within limit",
                limit=_RATE_LIMIT,
                count=10,
                expected_remaining="29990",
            ),
            _WithinWindowCase(
                description="exactly at limit",
                limit=_RATE_LIMIT,
                count=_RATE_LIMIT,
                expected_remaining="0",
            ),
            _WithinWindowCase(
                description="zero limit before any request lands",
                limit=0,
                count=0,
                expected_remaining="0",
            ),
            _WithinWindowCase(
                description="the limit fixed for the window outranks the injected one",
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
        mock_valkey_client: MagicMock,
        authorized_request: web.Request,
        mock_handler: AsyncMock,
        case: _WithinWindowCase,
    ) -> None:
        """The headers report the window that stands, not the limit the request carried."""
        # Arrange
        mock_valkey_client.consume_user_rate_limit.return_value = RateLimitState(
            count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act
        response = await middleware(authorized_request, mock_handler)
        await apply_reserved_response_headers(authorized_request, response)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == case.expected_remaining
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_called_once_with(authorized_request)

    @pytest.mark.parametrize("caller", [_ANONYMOUS, _AUTHORIZED], ids=lambda c: c.description)
    @pytest.mark.parametrize(
        "case",
        [
            _PastWindowCase(description="exceeds by 1", limit=_RATE_LIMIT, count=_RATE_LIMIT + 1),
            _PastWindowCase(description="far exceeds limit", limit=_RATE_LIMIT, count=50000),
            _PastWindowCase(description="zero limit always exceeds", limit=0, count=1),
        ],
        ids=lambda case: case.description,
    )
    async def test_a_request_past_its_window_is_refused(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        caller: _Caller,
        caller_request: web.Request,
        mock_handler: AsyncMock,
        case: _PastWindowCase,
    ) -> None:
        """Every caller is judged by the window it was counted in, and refused past it."""
        # Arrange
        getattr(mock_valkey_client, caller.consumer).return_value = RateLimitState(
            count=case.count, limit=case.limit, reset_after_seconds=_RESET_AFTER_SECONDS
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded), with_client_ip(_CLIENT_IP):
            await middleware(caller_request, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(caller_request, response)
        assert response.headers["X-RateLimit-Limit"] == str(case.limit)
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == str(_RESET_AFTER_SECONDS)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW_SECONDS)
        mock_handler.assert_not_called()

    async def test_an_anonymous_query_without_a_client_address_is_refused(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_handler: AsyncMock,
    ) -> None:
        """No address means no window to count in, and serving uncounted is not the answer."""
        # Arrange
        request = make_mocked_request("GET", "/")
        request.update(_ANONYMOUS.request_state)

        # Act & Assert
        with pytest.raises(UnreachableError):
            await middleware(request, mock_handler)
        mock_valkey_client.consume_ip_rate_limit.assert_not_called()
        mock_handler.assert_not_called()

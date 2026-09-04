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
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.web.reserved_response_headers import apply_reserved_response_headers
from ai.backend.manager.api.rest.ratelimit.handler import (
    _RATELIMIT_WINDOW,
    make_rlim_middleware,
)
from ai.backend.manager.errors.api import RateLimitExceeded

_USER_ID = UserID(uuid.UUID("12345678-1234-5678-1234-567812345678"))
_RESET = 500


@dataclass(frozen=True)
class RateLimitSuccessCase:
    state: RateLimitState
    expected_limit: str
    expected_remaining: str
    description: str = ""


@dataclass(frozen=True)
class RateLimitExceedCase:
    state: RateLimitState
    expected_limit: str
    description: str = ""


@dataclass(frozen=True)
class RateLimitPublishCase:
    keypair_rate_limit: int | None
    default_keypair_rate_limit: int | None


class TestRlimMiddleware:
    @pytest.fixture
    def mock_valkey_client(self) -> MagicMock:
        client = MagicMock(spec=ValkeyRateLimitClient)
        client.count_request = AsyncMock()
        return client

    @pytest.fixture
    def middleware(self, mock_valkey_client: MagicMock) -> Any:
        return make_rlim_middleware(mock_valkey_client)

    @pytest.fixture
    def mock_handler(self) -> AsyncMock:
        handler = AsyncMock()
        handler.return_value = web.Response(status=200, text="OK")
        return handler

    @pytest.fixture
    def mock_request_anonymous(self) -> web.Request:
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = False
        return request

    @pytest.fixture
    def mock_request_authorized(self) -> web.Request:
        request = make_mocked_request("GET", "/")
        request["is_authorized"] = True
        request["keypair"] = {"rate_limit": 30000}
        request["user"] = {"uuid": _USER_ID, "default_keypair_rate_limit": 30000}
        return request

    async def test_anonymous_query_returns_default_headers(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_anonymous: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        response = await middleware(mock_request_anonymous, mock_handler)
        await apply_reserved_response_headers(mock_request_anonymous, response)

        assert response.headers["X-RateLimit-Limit"] == "1000"
        assert response.headers["X-RateLimit-Remaining"] == "1000"
        assert response.headers["X-RateLimit-Reset"] == str(_RATELIMIT_WINDOW)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW)
        mock_handler.assert_called_once_with(mock_request_anonymous)
        mock_valkey_client.count_request.assert_not_called()

    @pytest.mark.parametrize(
        "test_case",
        [
            RateLimitSuccessCase(
                state=RateLimitState(count=10, limit=30000, reset=_RESET),
                expected_limit="30000",
                expected_remaining="29990",
                description="within limit",
            ),
            RateLimitSuccessCase(
                state=RateLimitState(count=30000, limit=30000, reset=_RESET),
                expected_limit="30000",
                expected_remaining="0",
                description="exactly at limit",
            ),
            RateLimitSuccessCase(
                state=RateLimitState(count=9999, limit=None, reset=_RESET),
                expected_limit="None",
                expected_remaining="9999",
                description="unlimited",
            ),
        ],
        ids=lambda tc: tc.description,
    )
    async def test_authorized_query_within_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        test_case: RateLimitSuccessCase,
    ) -> None:
        mock_valkey_client.count_request = AsyncMock(return_value=test_case.state)

        response = await middleware(mock_request_authorized, mock_handler)
        await apply_reserved_response_headers(mock_request_authorized, response)

        assert response.headers["X-RateLimit-Limit"] == test_case.expected_limit
        assert response.headers["X-RateLimit-Remaining"] == test_case.expected_remaining
        assert response.headers["X-RateLimit-Reset"] == str(_RESET)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW)
        mock_handler.assert_called_once_with(mock_request_authorized)
        mock_valkey_client.count_request.assert_called_once_with(
            user_id=_USER_ID,
            window=_RATELIMIT_WINDOW,
            rate_limit=30000,
        )

    @pytest.mark.parametrize(
        "case",
        [
            RateLimitPublishCase(keypair_rate_limit=30000, default_keypair_rate_limit=30000),
            RateLimitPublishCase(keypair_rate_limit=100, default_keypair_rate_limit=30000),
            RateLimitPublishCase(keypair_rate_limit=None, default_keypair_rate_limit=30000),
            RateLimitPublishCase(keypair_rate_limit=100, default_keypair_rate_limit=None),
        ],
        ids=lambda case: f"keypair={case.keypair_rate_limit}-default={case.default_keypair_rate_limit}",
    )
    async def test_the_default_keypair_limit_is_counted_whichever_keypair_signs(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        case: RateLimitPublishCase,
    ) -> None:
        mock_request_authorized["keypair"]["rate_limit"] = case.keypair_rate_limit
        mock_request_authorized["user"]["default_keypair_rate_limit"] = (
            case.default_keypair_rate_limit
        )
        mock_valkey_client.count_request = AsyncMock(
            return_value=RateLimitState(
                count=1, limit=case.default_keypair_rate_limit, reset=_RESET
            )
        )

        await middleware(mock_request_authorized, mock_handler)

        mock_valkey_client.count_request.assert_called_once_with(
            user_id=_USER_ID,
            window=_RATELIMIT_WINDOW,
            rate_limit=case.default_keypair_rate_limit,
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            RateLimitExceedCase(
                state=RateLimitState(count=30001, limit=30000, reset=_RESET),
                expected_limit="30000",
                description="exceeds by 1",
            ),
            RateLimitExceedCase(
                state=RateLimitState(count=50000, limit=30000, reset=_RESET),
                expected_limit="30000",
                description="far exceeds limit",
            ),
            RateLimitExceedCase(
                state=RateLimitState(count=1, limit=0, reset=_RESET),
                expected_limit="0",
                description="zero limit always exceeds",
            ),
        ],
        ids=lambda tc: tc.description,
    )
    async def test_authorized_query_exceeds_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_authorized: web.Request,
        mock_handler: AsyncMock,
        test_case: RateLimitExceedCase,
    ) -> None:
        mock_valkey_client.count_request = AsyncMock(return_value=test_case.state)

        with pytest.raises(RateLimitExceeded):
            await middleware(mock_request_authorized, mock_handler)
        response = web.Response(status=429)
        await apply_reserved_response_headers(mock_request_authorized, response)

        assert response.headers["X-RateLimit-Limit"] == test_case.expected_limit
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == str(_RESET)
        assert response.headers["X-RateLimit-Window"] == str(_RATELIMIT_WINDOW)
        mock_handler.assert_not_called()
        mock_valkey_client.count_request.assert_called_once_with(
            user_id=_USER_ID,
            window=_RATELIMIT_WINDOW,
            rate_limit=30000,
        )

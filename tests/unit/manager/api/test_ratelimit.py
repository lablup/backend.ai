from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.types import AccessKey, DefaultForUnspecified, ResourceSlot
from ai.backend.manager.api.rest.ratelimit.handler import _rlim_window, make_rlim_middleware
from ai.backend.manager.data.auth.types import AuthenticatedKeypair
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.errors.api import RateLimitExceeded


@dataclass
class RateLimitSuccessCase:
    """Test case data for successful rate limit scenarios."""

    rate_limit: int | None
    rolling_count: int
    expected_limit: str
    expected_remaining: str
    description: str = ""


@dataclass
class RateLimitExceedCase:
    """Test case data for rate limit exceeded scenarios."""

    rate_limit: int | None
    rolling_count: int
    description: str = ""


def _keypair_resource_policy() -> KeyPairResourcePolicyData:
    return KeyPairResourcePolicyData(
        name="default",
        created_at=None,
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots=ResourceSlot(),
        max_session_lifetime=0,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_priority=None,
        max_concurrent_sftp_sessions=2,
        max_containers_per_session=1,
        idle_timeout=3600,
        allowed_vfolder_hosts={},
    )


class TestRlimMiddleware:
    @pytest.fixture
    def mock_valkey_client(self) -> MagicMock:
        """Mock ValkeyRateLimitClient."""
        client = MagicMock(spec=ValkeyRateLimitClient)
        client.execute_rate_limit_logic = AsyncMock()
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
        request = MagicMock(spec=web.Request)
        request.__getitem__ = MagicMock(
            side_effect=lambda key: False if key == "is_authorized" else None
        )
        return request

    @pytest.fixture
    def authorized_request_factory(self) -> Callable[[int | None], web.Request]:
        """Build a mock request whose keypair carries the given rate limit."""

        def _make(rate_limit: int | None) -> web.Request:
            request = MagicMock(spec=web.Request)
            keypair = AuthenticatedKeypair(
                access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
                secret_key=None,
                is_admin=False,
                rate_limit=rate_limit,
                resource_policy=_keypair_resource_policy(),
            )

            def getitem(key: Any) -> Any:
                if key == "is_authorized":
                    return True
                if key == "keypair":
                    return keypair
                return None

            request.__getitem__ = MagicMock(side_effect=getitem)
            return request

        return _make

    async def test_anonymous_query_returns_default_headers(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        mock_request_anonymous: web.Request,
        mock_handler: AsyncMock,
    ) -> None:
        """Anonymous requests get default rate limit headers without Valkey check."""
        # Act
        response = await middleware(mock_request_anonymous, mock_handler)

        # Assert
        assert response.headers["X-RateLimit-Limit"] == "1000"
        assert response.headers["X-RateLimit-Remaining"] == "1000"
        assert response.headers["X-RateLimit-Window"] == str(_rlim_window)
        mock_handler.assert_called_once_with(mock_request_anonymous)

        # Valkey should not be called for anonymous requests
        mock_valkey_client.execute_rate_limit_logic.assert_not_called()

    @pytest.mark.parametrize(
        "test_case",
        [
            RateLimitSuccessCase(
                rate_limit=30000,
                rolling_count=10,
                expected_limit="30000",
                expected_remaining="29990",
                description="within limit",
            ),
            RateLimitSuccessCase(
                rate_limit=30000,
                rolling_count=30000,
                expected_limit="30000",
                expected_remaining="0",
                description="exactly at limit",
            ),
            RateLimitSuccessCase(
                rate_limit=None,
                rolling_count=9999,
                expected_limit="None",
                expected_remaining="9999",
                description="unlimited",
            ),
            RateLimitSuccessCase(
                rate_limit=None,
                rolling_count=999999,
                expected_limit="None",
                expected_remaining="999999",
                description="unlimited with very high count",
            ),
        ],
        ids=lambda tc: tc.description,
    )
    async def test_authorized_query_within_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        authorized_request_factory: Callable[[int | None], web.Request],
        mock_handler: AsyncMock,
        test_case: RateLimitSuccessCase,
    ) -> None:
        """Authorized requests within rate limit succeed and return correct headers."""
        # Arrange
        mock_request_authorized = authorized_request_factory(test_case.rate_limit)
        mock_valkey_client.execute_rate_limit_logic = AsyncMock(
            return_value=test_case.rolling_count
        )

        # Act
        response = await middleware(mock_request_authorized, mock_handler)

        # Assert headers
        assert response.headers["X-RateLimit-Limit"] == test_case.expected_limit
        assert response.headers["X-RateLimit-Remaining"] == test_case.expected_remaining
        assert response.headers["X-RateLimit-Window"] == str(_rlim_window)

        # Handler should be called
        mock_handler.assert_called_once_with(mock_request_authorized)

        # Valkey should be called for authorized requests
        mock_valkey_client.execute_rate_limit_logic.assert_called_once_with(
            access_key="AKIAIOSFODNN7EXAMPLE",
            window=_rlim_window,
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            RateLimitExceedCase(
                rate_limit=30000,
                rolling_count=30001,
                description="exceeds by 1",
            ),
            RateLimitExceedCase(
                rate_limit=30000,
                rolling_count=50000,
                description="far exceeds limit",
            ),
            RateLimitExceedCase(
                rate_limit=0,
                rolling_count=1,
                description="zero limit always exceeds",
            ),
        ],
        ids=lambda tc: tc.description,
    )
    async def test_authorized_query_exceeds_rate_limit(
        self,
        middleware: Any,
        mock_valkey_client: MagicMock,
        authorized_request_factory: Callable[[int | None], web.Request],
        mock_handler: AsyncMock,
        test_case: RateLimitExceedCase,
    ) -> None:
        """Authorized requests exceeding rate limit raise RateLimitExceeded."""
        # Arrange
        mock_request_authorized = authorized_request_factory(test_case.rate_limit)
        mock_valkey_client.execute_rate_limit_logic = AsyncMock(
            return_value=test_case.rolling_count
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await middleware(mock_request_authorized, mock_handler)

        # Handler should not be called when rate limit exceeded
        mock_handler.assert_not_called()

        # Valkey should still be called
        mock_valkey_client.execute_rate_limit_logic.assert_called_once_with(
            access_key="AKIAIOSFODNN7EXAMPLE",
            window=_rlim_window,
        )

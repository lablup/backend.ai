from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.health.exceptions import HttpHealthCheckError
from ai.backend.web.health.hive_router import HiveRouterHealthChecker


class TestHiveRouterHealthChecker:
    """Test HiveRouterHealthChecker with mocked HTTP session."""

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        """Test successful health check."""
        # Mock aiohttp.ClientSession
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = HTTPStatus.OK
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        checker = HiveRouterHealthChecker(
            url="http://localhost:8080",
            session=mock_session,
            timeout=5.0,
        )

        # Should not raise
        await checker.check_health()

        # Verify request was made to /health endpoint
        mock_session.request.assert_called_once_with(
            "GET",
            "http://localhost:8080/health",
        )

    @pytest.mark.asyncio
    async def test_timeout_property(self) -> None:
        """Test that timeout property returns the correct value."""
        mock_session = MagicMock()
        timeout_value = 3.5
        checker = HiveRouterHealthChecker(
            url="http://localhost:8080",
            session=mock_session,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.asyncio
    async def test_http_error(self) -> None:
        """Test health check failure with HTTP error status."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = HTTPStatus.SERVICE_UNAVAILABLE
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        checker = HiveRouterHealthChecker(
            url="http://localhost:8080",
            session=mock_session,
            timeout=5.0,
        )

        with pytest.raises(HttpHealthCheckError):
            await checker.check_health()

    @pytest.mark.asyncio
    async def test_url_with_trailing_slash(self) -> None:
        """Test that URL with trailing slash is handled correctly."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = HTTPStatus.OK
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        checker = HiveRouterHealthChecker(
            url="http://localhost:8080/",
            session=mock_session,
            timeout=5.0,
        )

        await checker.check_health()

        # Should remove trailing slash before appending /health
        mock_session.request.assert_called_once_with(
            "GET",
            "http://localhost:8080/health",
        )

    @pytest.mark.asyncio
    async def test_multiple_checks(self) -> None:
        """Test that multiple health checks work correctly."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = HTTPStatus.OK
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        checker = HiveRouterHealthChecker(
            url="http://localhost:8080",
            session=mock_session,
            timeout=5.0,
        )

        # Multiple checks should all succeed
        await checker.check_health()
        await checker.check_health()
        await checker.check_health()

        # request should have been called 3 times
        assert mock_session.request.call_count == 3

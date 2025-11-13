from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from http import HTTPMethod

import aiohttp
import pytest
from aiohttp import web

from ai.backend.common.health.checkers.http import HttpHealthChecker
from ai.backend.common.health.exceptions import HttpHealthCheckError


class TestHttpHealthChecker:
    """Test HttpHealthChecker with various HTTP scenarios."""

    @pytest.fixture
    async def aiohttp_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """Provides an aiohttp ClientSession for testing."""
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.fixture
    async def http_test_server(self) -> AsyncGenerator[str, None]:
        """
        Runs a test HTTP server with various endpoints for testing HttpHealthChecker.

        Endpoints:
        - GET /health - Returns 200 OK
        - POST /health - Returns 200 OK
        - HEAD /health - Returns 200 OK
        - OPTIONS /health - Returns 200 OK
        - GET /health_204 - Returns 204 No Content
        - GET /error - Returns 500 Internal Server Error
        - GET /not_found - Returns 404 Not Found
        - GET /slow - Sleeps for 10 seconds before returning 200
        """
        app = web.Application()

        async def health_ok(request: web.Request) -> web.Response:
            return web.Response(status=200, text="OK")

        async def health_204(request: web.Request) -> web.Response:
            return web.Response(status=204)

        async def health_error(request: web.Request) -> web.Response:
            return web.Response(status=500, text="Internal Server Error")

        async def health_not_found(request: web.Request) -> web.Response:
            return web.Response(status=404, text="Not Found")

        async def health_slow(request: web.Request) -> web.Response:
            await asyncio.sleep(10)
            return web.Response(status=200, text="OK")

        app.router.add_get("/health", health_ok)
        app.router.add_post("/health", health_ok)
        # HEAD is automatically added by aiohttp when GET is present
        app.router.add_route("OPTIONS", "/health", health_ok)
        app.router.add_get("/health_204", health_204)
        app.router.add_get("/error", health_error)
        app.router.add_get("/not_found", health_not_found)
        app.router.add_get("/slow", health_slow)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()

        # Get the dynamically assigned port
        assert site._server is not None
        port = site._server.sockets[0].getsockname()[1]  # type: ignore[attr-defined]
        url = f"http://127.0.0.1:{port}"

        yield url

        await runner.cleanup()

    @pytest.mark.asyncio
    async def test_success_get(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with GET method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            session=aiohttp_session,
            timeout=5.0,
        )

        # Should not raise
        await checker.check_health()

    @pytest.mark.asyncio
    async def test_success_post(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with POST method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            session=aiohttp_session,
            method=HTTPMethod.POST,
            timeout=5.0,
        )

        await checker.check_health()

    @pytest.mark.asyncio
    async def test_success_head(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with HEAD method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            session=aiohttp_session,
            method=HTTPMethod.HEAD,
            timeout=5.0,
        )

        await checker.check_health()

    @pytest.mark.asyncio
    async def test_success_options(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with OPTIONS method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            session=aiohttp_session,
            method=HTTPMethod.OPTIONS,
            timeout=5.0,
        )

        await checker.check_health()

    @pytest.mark.asyncio
    async def test_custom_status_codes(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with custom expected status codes."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health_204",
            session=aiohttp_session,
            expected_status_codes=[200, 204],
            timeout=5.0,
        )

        # 204 is in expected_status_codes, should not raise
        await checker.check_health()

    @pytest.mark.asyncio
    async def test_unexpected_status_code(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with unexpected status code."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/error",
            session=aiohttp_session,
            timeout=5.0,
        )

        with pytest.raises(HttpHealthCheckError) as exc_info:
            await checker.check_health()

        assert "returned status 500" in str(exc_info.value)
        assert "expected one of [200]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with 404 Not Found."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/not_found",
            session=aiohttp_session,
            timeout=5.0,
        )

        with pytest.raises(HttpHealthCheckError) as exc_info:
            await checker.check_health()

        assert "returned status 404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check timeout."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/slow",
            session=aiohttp_session,
            timeout=0.5,  # Short timeout
        )

        with pytest.raises(HttpHealthCheckError) as exc_info:
            await checker.check_health()

        assert "timed out" in str(exc_info.value).lower()
        assert "0.5s" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connection_error(
        self,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with connection error."""
        # Use a non-existent server
        checker = HttpHealthChecker(
            url="http://localhost:99999/health",
            session=aiohttp_session,
            timeout=2.0,
        )

        with pytest.raises(HttpHealthCheckError) as exc_info:
            await checker.check_health()

        # Should contain error information
        assert "health check failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_timeout_property(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            session=aiohttp_session,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.asyncio
    async def test_method_in_error_message(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test that HTTP method is included in error messages."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/error",
            session=aiohttp_session,
            method=HTTPMethod.POST,
            timeout=5.0,
        )

        with pytest.raises(HttpHealthCheckError) as exc_info:
            await checker.check_health()

        # Error message should include the HTTP method
        assert "POST" in str(exc_info.value)

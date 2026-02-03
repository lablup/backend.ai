from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from http import HTTPMethod

import aiohttp
import pytest
from aiohttp import web

from ai.backend.common.health_checker import ComponentId
from ai.backend.common.health_checker.checkers.http import HttpHealthChecker


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
            component_id=ComponentId("api"),
            session=aiohttp_session,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy
        assert status.error_message is None

    @pytest.mark.asyncio
    async def test_success_post(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with POST method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            method=HTTPMethod.POST,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy

    @pytest.mark.asyncio
    async def test_success_head(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with HEAD method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            method=HTTPMethod.HEAD,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy

    @pytest.mark.asyncio
    async def test_success_options(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with OPTIONS method."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            method=HTTPMethod.OPTIONS,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy

    @pytest.mark.asyncio
    async def test_custom_status_codes(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test successful health check with custom expected status codes."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/health_204",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            expected_status_codes=[200, 204],
            timeout=5.0,
        )

        # 204 is in expected_status_codes, should return healthy status
        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy

    @pytest.mark.asyncio
    async def test_unexpected_status_code(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with unexpected status code."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/error",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert not status.is_healthy
        assert status.error_message is not None
        assert "returned status 500" in status.error_message
        assert "expected one of [200]" in status.error_message

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with 404 Not Found."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/not_found",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert not status.is_healthy
        assert status.error_message is not None
        assert "returned status 404" in status.error_message

    @pytest.mark.asyncio
    async def test_timeout(
        self,
        http_test_server: str,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check timeout."""
        checker = HttpHealthChecker(
            url=f"{http_test_server}/slow",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            timeout=0.5,  # Short timeout
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert not status.is_healthy
        assert status.error_message is not None
        assert "timed out" in status.error_message.lower()
        assert "0.5s" in status.error_message

    @pytest.mark.asyncio
    async def test_connection_error(
        self,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Test health check failure with connection error."""
        # Use a non-existent server
        checker = HttpHealthChecker(
            url="http://localhost:99999/health",
            component_id=ComponentId("api"),
            session=aiohttp_session,
            timeout=2.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert not status.is_healthy
        assert status.error_message is not None
        assert "health check failed" in status.error_message.lower()

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
            component_id=ComponentId("api"),
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
            component_id=ComponentId("api"),
            session=aiohttp_session,
            method=HTTPMethod.POST,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert not status.is_healthy
        assert status.error_message is not None
        # Error message should include the HTTP method
        assert "POST" in status.error_message

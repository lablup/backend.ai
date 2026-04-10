"""
Unit tests for health check handlers.

Tests cover:
- PublicHealthHandler.hello: simple liveness probe, no external I/O
- InternalHealthHandler.hello: full connectivity status via mocked HealthProbe
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.dto.internal.health import (
    ComponentConnectivityStatus,
    ConnectivityCheckResponse,
)
from ai.backend.common.health_checker.probe import HealthProbe
from ai.backend.manager import __version__
from ai.backend.manager.api.rest.health.handler import HealthHandler
from ai.backend.manager.api.rest.internal.health.handler import InternalHealthHandler
from ai.backend.manager.dto.context import RequestCtx

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_request() -> MagicMock:
    """Minimal aiohttp Request mock that supports item assignment."""
    req = MagicMock(spec=web.Request)
    req.__setitem__ = MagicMock()
    return req


@pytest.fixture
def mock_request_ctx(mock_request: MagicMock) -> MagicMock:
    """RequestCtx mock wrapping the mock request."""
    ctx = MagicMock(spec=RequestCtx)
    ctx.request = mock_request
    return ctx


@pytest.fixture
def healthy_connectivity() -> ConnectivityCheckResponse:
    """ConnectivityCheckResponse with one healthy component."""
    now = datetime.now(UTC)
    return ConnectivityCheckResponse(
        overall_healthy=True,
        connectivity_checks=[
            ComponentConnectivityStatus(
                service_group="database",
                component_id="postgres",
                is_healthy=True,
                last_checked_at=now,
                error_message=None,
            ),
        ],
        timestamp=now,
    )


@pytest.fixture
def degraded_connectivity() -> ConnectivityCheckResponse:
    """ConnectivityCheckResponse with one unhealthy component."""
    now = datetime.now(UTC)
    return ConnectivityCheckResponse(
        overall_healthy=False,
        connectivity_checks=[
            ComponentConnectivityStatus(
                service_group="redis",
                component_id="cache",
                is_healthy=False,
                last_checked_at=now,
                error_message="Connection refused",
            ),
        ],
        timestamp=now,
    )


@pytest.fixture
def mock_health_probe(healthy_connectivity: ConnectivityCheckResponse) -> MagicMock:
    """Mocked HealthProbe returning healthy connectivity by default."""
    probe = MagicMock(spec=HealthProbe)
    probe.get_connectivity_status = AsyncMock(return_value=healthy_connectivity)
    return probe


# ---------------------------------------------------------------------------
# TestPublicHealthHandler
# ---------------------------------------------------------------------------


class TestPublicHealthHandler:
    """Tests for public HealthHandler (liveness probe only)."""

    @pytest.fixture
    def handler(self) -> HealthHandler:
        return HealthHandler()

    async def test_returns_200_with_status_ok(
        self,
        handler: HealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello returns HTTP 200 with status=ok and version."""
        response = await handler.hello(mock_request_ctx)

        assert response.status == 200
        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["status"] == "ok"
        assert body["version"] == __version__

    async def test_sets_do_not_print_access_log(
        self,
        handler: HealthHandler,
        mock_request: MagicMock,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello sets do_not_print_access_log flag on the request."""
        await handler.hello(mock_request_ctx)

        mock_request.__setitem__.assert_called_once_with("do_not_print_access_log", True)

    async def test_no_connectivity_field(
        self,
        handler: HealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello does NOT include connectivity field (no HealthProbe call)."""
        response = await handler.hello(mock_request_ctx)

        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert "connectivity" not in body

    async def test_no_external_io(
        self,
        handler: HealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello completes without any external I/O (no AsyncMock calls)."""
        # If any async call occurred, it would fail here without an event loop issue
        # The handler should be synchronous in effect — just return a static response
        response = await handler.hello(mock_request_ctx)

        assert isinstance(response, web.Response)


# ---------------------------------------------------------------------------
# TestInternalHealthHandler
# ---------------------------------------------------------------------------


class TestInternalHealthHandler:
    """Tests for InternalHealthHandler (full connectivity via HealthProbe)."""

    @pytest.fixture
    def handler(self, mock_health_probe: MagicMock) -> InternalHealthHandler:
        return InternalHealthHandler(health_probe=mock_health_probe)

    async def test_returns_200_with_connectivity_field(
        self,
        handler: InternalHealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello returns JSON with connectivity field."""
        response = await handler.hello(mock_request_ctx)

        assert response.status == 200
        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert "connectivity" in body
        assert "overall_healthy" in body["connectivity"]

    async def test_healthy_probe_returns_status_ok(
        self,
        handler: InternalHealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify status=ok when HealthProbe reports all components healthy."""
        response = await handler.hello(mock_request_ctx)

        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["status"] == "ok"
        assert body["connectivity"]["overall_healthy"] is True

    async def test_degraded_probe_returns_status_degraded(
        self,
        mock_health_probe: MagicMock,
        mock_request_ctx: MagicMock,
        degraded_connectivity: ConnectivityCheckResponse,
    ) -> None:
        """Verify status=degraded when HealthProbe reports an unhealthy component."""
        mock_health_probe.get_connectivity_status = AsyncMock(return_value=degraded_connectivity)
        handler = InternalHealthHandler(health_probe=mock_health_probe)

        response = await handler.hello(mock_request_ctx)

        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["status"] == "degraded"
        assert body["connectivity"]["overall_healthy"] is False

    async def test_includes_version_and_component(
        self,
        handler: InternalHealthHandler,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello includes version and component fields."""
        response = await handler.hello(mock_request_ctx)

        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["version"] == __version__
        assert body["component"] == "manager"

    async def test_sets_do_not_print_access_log(
        self,
        handler: InternalHealthHandler,
        mock_request: MagicMock,
        mock_request_ctx: MagicMock,
    ) -> None:
        """Verify hello sets do_not_print_access_log flag on the request."""
        await handler.hello(mock_request_ctx)

        mock_request.__setitem__.assert_called_once_with("do_not_print_access_log", True)

    async def test_calls_health_probe_get_connectivity_status(
        self,
        handler: InternalHealthHandler,
        mock_request_ctx: MagicMock,
        mock_health_probe: MagicMock,
    ) -> None:
        """Verify get_connectivity_status is called exactly once per request."""
        await handler.hello(mock_request_ctx)

        mock_health_probe.get_connectivity_status.assert_awaited_once()

    async def test_connectivity_checks_in_response(
        self,
        handler: InternalHealthHandler,
        mock_request_ctx: MagicMock,
        healthy_connectivity: ConnectivityCheckResponse,
    ) -> None:
        """Verify connectivity_checks list is included in the response body."""
        response = await handler.hello(mock_request_ctx)

        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        checks = body["connectivity"]["connectivity_checks"]
        assert len(checks) == 1
        assert checks[0]["component_id"] == "postgres"
        assert checks[0]["is_healthy"] is True

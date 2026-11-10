"""Unit tests for ServiceCatalogEventHandler."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.events.event_types.service_discovery.anycast import (
    DoSweepStaleServicesEvent,
    ServiceDeregisteredEvent,
    ServiceEndpointInfo,
    ServiceRegisteredEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.event_dispatcher.handlers.service_catalog import (
    ServiceCatalogEventHandler,
)
from ai.backend.manager.models.service_catalog.creators import ServiceCatalogEndpointCreator
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter


def _make_mock_db(mock_session: AsyncMock) -> MagicMock:
    """Create a mock db engine whose begin_session() yields the given session."""
    mock_db = MagicMock()

    @asynccontextmanager
    async def _begin_session(**kwargs: Any) -> AsyncIterator[AsyncMock]:
        yield mock_session

    mock_db.begin_session = _begin_session
    return mock_db


@pytest.fixture
def sample_registered_event() -> ServiceRegisteredEvent:
    return ServiceRegisteredEvent(
        instance_id="mgr-001",
        service_group="manager",
        display_name="Manager Instance 1",
        version="26.3.0",
        labels={"region": "us-east-1"},
        endpoints=[
            ServiceEndpointInfo(
                role="main",
                scope="private",
                address="10.0.0.1",
                port=8080,
                protocol="grpc",
                metadata={},
            ),
            ServiceEndpointInfo(
                role="health",
                scope="internal",
                address="10.0.0.1",
                port=8081,
                protocol="http",
                metadata={"path": "/healthz"},
            ),
        ],
        startup_time=datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC),
        config_hash="abc123",
    )


@pytest.fixture
def sample_deregistered_event() -> ServiceDeregisteredEvent:
    return ServiceDeregisteredEvent(
        instance_id="mgr-001",
        service_group="manager",
    )


class TestHandleRegistered:
    """Tests for handle_registered method."""

    async def test_registers_service_with_its_endpoints(
        self,
        sample_registered_event: ServiceRegisteredEvent,
    ) -> None:
        """handle_registered hands the instance and every announced endpoint to the repository."""
        repository = AsyncMock()
        handler = ServiceCatalogEventHandler(db=MagicMock(), repository=repository)

        await handler.handle_registered(None, AgentId("i-test"), sample_registered_event)

        repository.register.assert_awaited_once()
        upserter, endpoints = repository.register.await_args.args
        assert isinstance(upserter, ServiceCatalogUpserter)
        assert (upserter.service_group, upserter.instance_id) == ("manager", "mgr-001")
        assert [
            (endpoint.role, endpoint.scope)
            for endpoint in endpoints
            if isinstance(endpoint, ServiceCatalogEndpointCreator)
        ] == [("main", "private"), ("health", "internal")]

    async def test_no_endpoints_registers_none(self) -> None:
        """handle_registered with no endpoints passes an empty endpoint list."""
        event = ServiceRegisteredEvent(
            instance_id="agent-001",
            service_group="agent",
            display_name="Agent 1",
            version="26.3.0",
            endpoints=[],
            startup_time=datetime.now(tz=UTC),
        )
        repository = AsyncMock()
        handler = ServiceCatalogEventHandler(db=MagicMock(), repository=repository)

        await handler.handle_registered(None, AgentId("i-test"), event)

        _, endpoints = repository.register.await_args.args
        assert endpoints == []


class TestHandleDeregistered:
    """Tests for handle_deregistered method."""

    async def test_updates_status_to_deregistered(
        self,
        sample_deregistered_event: ServiceDeregisteredEvent,
    ) -> None:
        """handle_deregistered should update the service status to DEREGISTERED."""
        mock_session = AsyncMock()
        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db, repository=AsyncMock())

        await handler.handle_deregistered(
            None,
            AgentId("i-test"),
            sample_deregistered_event,
        )

        mock_session.execute.assert_called_once()


class TestSweepStaleServices:
    """Tests for sweep stale services functionality."""

    async def test_sweep_marks_stale_services(self) -> None:
        """_sweep_stale_services should update stale HEALTHY services to UNHEALTHY."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db, repository=AsyncMock())

        count = await handler._sweep_stale_services(threshold_minutes=5)

        assert count == 3
        mock_session.execute.assert_called_once()

    async def test_sweep_returns_zero_when_no_stale(self) -> None:
        """_sweep_stale_services should return 0 when no stale services found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db, repository=AsyncMock())

        count = await handler._sweep_stale_services()

        assert count == 0

    async def test_handle_sweep_delegates_to_sweep(self) -> None:
        """handle_sweep_stale_services should delegate to _sweep_stale_services."""
        handler = ServiceCatalogEventHandler(db=MagicMock(), repository=AsyncMock())
        with patch.object(handler, "_sweep_stale_services", new_callable=AsyncMock) as mock_sweep:
            mock_sweep.return_value = 2
            await handler.handle_sweep_stale_services(
                None,
                AgentId("i-test"),
                DoSweepStaleServicesEvent(),
            )
            mock_sweep.assert_called_once()

"""Unit tests for ServiceCatalogEventHandler."""

from __future__ import annotations

import uuid
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

    async def test_upserts_service_and_endpoints(
        self,
        sample_registered_event: ServiceRegisteredEvent,
    ) -> None:
        """handle_registered should execute upsert, delete old endpoints, insert new ones."""
        service_id = uuid.uuid4()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = service_id
        mock_session.execute = AsyncMock(side_effect=[mock_result, None, None])

        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db)

        await handler.handle_registered(
            None,
            AgentId("i-test"),
            sample_registered_event,
        )

        # Should have 3 execute calls: upsert, delete endpoints, insert endpoints
        assert mock_session.execute.call_count == 3

    async def test_no_endpoints_skips_insert(self) -> None:
        """handle_registered with no endpoints should skip the insert."""
        event = ServiceRegisteredEvent(
            instance_id="agent-001",
            service_group="agent",
            display_name="Agent 1",
            version="26.3.0",
            endpoints=[],
            startup_time=datetime.now(tz=UTC),
        )

        service_id = uuid.uuid4()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = service_id
        mock_session.execute = AsyncMock(side_effect=[mock_result, None])

        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db)

        await handler.handle_registered(None, AgentId("i-test"), event)

        # Should have 2 execute calls: upsert, delete endpoints (no insert)
        assert mock_session.execute.call_count == 2


class TestHandleDeregistered:
    """Tests for handle_deregistered method."""

    async def test_updates_status_to_deregistered(
        self,
        sample_deregistered_event: ServiceDeregisteredEvent,
    ) -> None:
        """handle_deregistered should update the service status to DEREGISTERED."""
        mock_session = AsyncMock()
        mock_db = _make_mock_db(mock_session)
        handler = ServiceCatalogEventHandler(db=mock_db)

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
        handler = ServiceCatalogEventHandler(db=mock_db)

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
        handler = ServiceCatalogEventHandler(db=mock_db)

        count = await handler._sweep_stale_services()

        assert count == 0

    async def test_handle_sweep_delegates_to_sweep(self) -> None:
        """handle_sweep_stale_services should delegate to _sweep_stale_services."""
        mock_db = MagicMock()
        handler = ServiceCatalogEventHandler(db=mock_db)
        with patch.object(handler, "_sweep_stale_services", new_callable=AsyncMock) as mock_sweep:
            mock_sweep.return_value = 2
            await handler.handle_sweep_stale_services(
                None,
                AgentId("i-test"),
                DoSweepStaleServicesEvent(),
            )
            mock_sweep.assert_called_once()

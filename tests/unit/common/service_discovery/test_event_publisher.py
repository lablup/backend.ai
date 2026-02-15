"""Unit tests for ServiceDiscoveryEventPublisher."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.configs.service_discovery import (
    ServiceDiscoveryConfig,
    ServiceEndpointConfig,
)
from ai.backend.common.events.event_types.service_discovery.anycast import (
    ServiceDeregisteredEvent,
    ServiceRegisteredEvent,
)
from ai.backend.common.service_discovery.event_publisher import (
    ServiceDiscoveryEventPublisher,
)
from ai.backend.common.types import ServiceDiscoveryType


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    producer = AsyncMock()
    producer.anycast_event = AsyncMock()
    return producer


@pytest.fixture
def sd_config() -> ServiceDiscoveryConfig:
    return ServiceDiscoveryConfig(
        type=ServiceDiscoveryType.REDIS,
        instance_id="test-instance-001",
        service_group="manager",
        display_name="Test Manager",
        extra_labels={"region": "us-east-1"},
        endpoints=[
            ServiceEndpointConfig(
                role="main",
                scope="private",
                address="127.0.0.1",
                port=8080,
                protocol="http",
                metadata={},
            ),
            ServiceEndpointConfig(
                role="health",
                scope="internal",
                address="127.0.0.1",
                port=8081,
                protocol="http",
                metadata={},
            ),
        ],
    )


@pytest.fixture
def startup_time() -> datetime:
    return datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def publisher(
    mock_event_producer: AsyncMock,
    sd_config: ServiceDiscoveryConfig,
    startup_time: datetime,
) -> ServiceDiscoveryEventPublisher:
    return ServiceDiscoveryEventPublisher(
        event_producer=mock_event_producer,
        config=sd_config,
        component_version="26.3.0",
        startup_time=startup_time,
    )


class TestServiceDiscoveryEventPublisher:
    """Tests for ServiceDiscoveryEventPublisher."""

    async def test_publish_registered_sends_correct_event(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """publish_registered should build and send ServiceRegisteredEvent."""
        await publisher.publish_registered()

        mock_event_producer.anycast_event.assert_called_once()
        event = mock_event_producer.anycast_event.call_args[0][0]
        assert isinstance(event, ServiceRegisteredEvent)
        assert event.instance_id == "test-instance-001"
        assert event.service_group == "manager"
        assert event.display_name == "Test Manager"
        assert event.version == "26.3.0"
        assert event.labels == {"region": "us-east-1"}
        assert len(event.endpoints) == 2

    async def test_publish_registered_builds_endpoints(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """Endpoints from config should be correctly mapped to ServiceEndpointInfo."""
        await publisher.publish_registered()

        event = mock_event_producer.anycast_event.call_args[0][0]
        ep_main = event.endpoints[0]
        assert ep_main.role == "main"
        assert ep_main.scope == "private"
        assert ep_main.address == "127.0.0.1"
        assert ep_main.port == 8080
        assert ep_main.protocol == "http"

        ep_health = event.endpoints[1]
        assert ep_health.role == "health"
        assert ep_health.scope == "internal"
        assert ep_health.port == 8081

    async def test_publish_deregistered_sends_correct_event(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """publish_deregistered should build and send ServiceDeregisteredEvent."""
        await publisher.publish_deregistered()

        mock_event_producer.anycast_event.assert_called_once()
        event = mock_event_producer.anycast_event.call_args[0][0]
        assert isinstance(event, ServiceDeregisteredEvent)
        assert event.instance_id == "test-instance-001"
        assert event.service_group == "manager"

    async def test_start_publishes_initial_registration(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """start() should immediately publish a registration event."""
        await publisher.start(heartbeat_interval=60)
        try:
            # First call should be the initial registration
            assert mock_event_producer.anycast_event.call_count == 1
            event = mock_event_producer.anycast_event.call_args[0][0]
            assert isinstance(event, ServiceRegisteredEvent)
        finally:
            await publisher.stop()

    async def test_stop_publishes_deregistration(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """stop() should publish a deregistered event."""
        await publisher.start(heartbeat_interval=60)
        mock_event_producer.anycast_event.reset_mock()
        await publisher.stop()

        # The last call should be deregistered
        mock_event_producer.anycast_event.assert_called_once()
        event = mock_event_producer.anycast_event.call_args[0][0]
        assert isinstance(event, ServiceDeregisteredEvent)

    async def test_stop_cancels_heartbeat_task(
        self,
        publisher: ServiceDiscoveryEventPublisher,
        mock_event_producer: AsyncMock,
    ) -> None:
        """stop() should cancel the heartbeat task."""
        await publisher.start(heartbeat_interval=60)
        assert publisher._heartbeat_task is not None
        assert not publisher._heartbeat_task.done()

        await publisher.stop()
        # Give event loop a cycle
        await asyncio.sleep(0)
        assert publisher._heartbeat_task.done()

    async def test_config_with_no_endpoints(
        self,
        mock_event_producer: AsyncMock,
    ) -> None:
        """Publisher should handle config with no endpoints."""
        config = ServiceDiscoveryConfig(
            type=ServiceDiscoveryType.REDIS,
            instance_id="no-endpoints",
            service_group="agent",
            display_name="Test Agent",
            extra_labels={},
            endpoints=[],
        )
        pub = ServiceDiscoveryEventPublisher(
            event_producer=mock_event_producer,
            config=config,
            component_version="26.3.0",
            startup_time=datetime.now(tz=UTC),
        )
        await pub.publish_registered()

        event = mock_event_producer.anycast_event.call_args[0][0]
        assert event.endpoints == []

    async def test_config_with_none_fields_defaults_to_empty_string(
        self,
        mock_event_producer: AsyncMock,
    ) -> None:
        """Config fields that are None should default to empty strings in events."""
        config = ServiceDiscoveryConfig(
            type=ServiceDiscoveryType.REDIS,
            instance_id=None,
            service_group=None,
            display_name=None,
            extra_labels={},
            endpoints=[],
        )
        pub = ServiceDiscoveryEventPublisher(
            event_producer=mock_event_producer,
            config=config,
            component_version="26.3.0",
            startup_time=datetime.now(tz=UTC),
        )
        await pub.publish_registered()

        event = mock_event_producer.anycast_event.call_args[0][0]
        assert event.instance_id == ""
        assert event.service_group == ""
        assert event.display_name == ""

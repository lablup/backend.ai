from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.events.event_types.service_discovery.anycast import (
    ServiceDeregisteredEvent,
    ServiceEndpointInfo,
    ServiceRegisteredEvent,
)
from ai.backend.common.events.types import EventDomain


class TestServiceRegisteredEvent:
    """Tests for ServiceRegisteredEvent serialization and metadata."""

    def test_event_name(self) -> None:
        assert ServiceRegisteredEvent.event_name() == "service_registered"

    def test_event_domain(self) -> None:
        assert ServiceRegisteredEvent.event_domain() == EventDomain.SERVICE_DISCOVERY

    def test_serialize_deserialize_roundtrip(self) -> None:
        startup = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
        event = ServiceRegisteredEvent(
            instance_id="manager-001",
            service_group="manager",
            display_name="Manager Instance 1",
            version="26.3.0",
            labels={"region": "us-west-2"},
            endpoints=[
                ServiceEndpointInfo(
                    role="main",
                    scope="public",
                    address="manager.example.com",
                    port=443,
                    protocol="https",
                    metadata={"weight": "100"},
                ),
            ],
            startup_time=startup,
            config_hash="abc123",
        )

        serialized = event.serialize()
        assert isinstance(serialized, tuple)
        assert len(serialized) == 2

        restored = ServiceRegisteredEvent.deserialize(serialized)
        assert restored.instance_id == "manager-001"
        assert restored.service_group == "manager"
        assert restored.display_name == "Manager Instance 1"
        assert restored.version == "26.3.0"
        assert restored.labels == {"region": "us-west-2"}
        assert len(restored.endpoints) == 1
        assert restored.endpoints[0].role == "main"
        assert restored.endpoints[0].port == 443
        assert restored.endpoints[0].metadata == {"weight": "100"}
        assert restored.startup_time == startup
        assert restored.config_hash == "abc123"

    def test_serialize_deserialize_minimal(self) -> None:
        startup = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
        event = ServiceRegisteredEvent(
            instance_id="agent-001",
            service_group="agent",
            display_name="Agent 1",
            version="26.3.0",
            startup_time=startup,
        )

        restored = ServiceRegisteredEvent.deserialize(event.serialize())
        assert restored.instance_id == "agent-001"
        assert restored.labels == {}
        assert restored.endpoints == []
        assert restored.config_hash == ""

    def test_domain_id_is_none(self) -> None:
        event = ServiceRegisteredEvent(
            instance_id="test",
            service_group="test",
            display_name="Test",
            version="1.0",
            startup_time=datetime.now(tz=UTC),
        )
        assert event.domain_id() is None

    def test_user_event_is_none(self) -> None:
        event = ServiceRegisteredEvent(
            instance_id="test",
            service_group="test",
            display_name="Test",
            version="1.0",
            startup_time=datetime.now(tz=UTC),
        )
        assert event.user_event() is None


class TestServiceDeregisteredEvent:
    """Tests for ServiceDeregisteredEvent serialization and metadata."""

    def test_event_name(self) -> None:
        assert ServiceDeregisteredEvent.event_name() == "service_deregistered"

    def test_event_domain(self) -> None:
        assert ServiceDeregisteredEvent.event_domain() == EventDomain.SERVICE_DISCOVERY

    def test_serialize_deserialize_roundtrip(self) -> None:
        event = ServiceDeregisteredEvent(
            instance_id="manager-001",
            service_group="manager",
        )

        serialized = event.serialize()
        assert isinstance(serialized, tuple)
        assert len(serialized) == 2

        restored = ServiceDeregisteredEvent.deserialize(serialized)
        assert restored.instance_id == "manager-001"
        assert restored.service_group == "manager"

    def test_domain_id_is_none(self) -> None:
        event = ServiceDeregisteredEvent(
            instance_id="test",
            service_group="test",
        )
        assert event.domain_id() is None

    def test_user_event_is_none(self) -> None:
        event = ServiceDeregisteredEvent(
            instance_id="test",
            service_group="test",
        )
        assert event.user_event() is None

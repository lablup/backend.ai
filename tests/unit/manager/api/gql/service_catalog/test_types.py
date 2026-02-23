"""Unit tests for service catalog GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.service_catalog.types import (
    ServiceCatalogEndpointGQL,
    ServiceCatalogFilterGQL,
    ServiceCatalogGQL,
    ServiceCatalogStatusGQL,
)
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)


class TestServiceCatalogStatusGQL:
    """Tests for ServiceCatalogStatusGQL enum."""

    def test_from_status_healthy(self) -> None:
        result = ServiceCatalogStatusGQL.from_status(ServiceCatalogStatus.HEALTHY)
        assert result == ServiceCatalogStatusGQL.HEALTHY

    def test_from_status_unhealthy(self) -> None:
        result = ServiceCatalogStatusGQL.from_status(ServiceCatalogStatus.UNHEALTHY)
        assert result == ServiceCatalogStatusGQL.UNHEALTHY

    def test_from_status_deregistered(self) -> None:
        result = ServiceCatalogStatusGQL.from_status(ServiceCatalogStatus.DEREGISTERED)
        assert result == ServiceCatalogStatusGQL.DEREGISTERED


class TestServiceCatalogEndpointGQL:
    """Tests for ServiceCatalogEndpointGQL type."""

    def test_from_data(self) -> None:
        """from_data should correctly map all endpoint fields."""
        data = ServiceCatalogEndpointData(
            id=uuid.uuid4(),
            service_id=uuid.uuid4(),
            role="main",
            scope="private",
            address="10.0.0.1",
            port=8080,
            protocol="grpc",
            metadata={"key": "value"},
        )

        endpoint = ServiceCatalogEndpointGQL.from_data(data)

        assert endpoint.role == "main"
        assert endpoint.scope == "private"
        assert endpoint.address == "10.0.0.1"
        assert endpoint.port == 8080
        assert endpoint.protocol == "grpc"
        assert endpoint.metadata == {"key": "value"}

    def test_from_data_null_metadata(self) -> None:
        """from_data should handle None metadata."""
        data = ServiceCatalogEndpointData(
            id=uuid.uuid4(),
            service_id=uuid.uuid4(),
            role="health",
            scope="internal",
            address="127.0.0.1",
            port=8081,
            protocol="http",
            metadata=None,
        )

        endpoint = ServiceCatalogEndpointGQL.from_data(data)

        assert endpoint.metadata is None


class TestServiceCatalogGQL:
    """Tests for ServiceCatalogGQL type."""

    def test_from_data(self) -> None:
        """from_data should correctly map all catalog fields including nested endpoints."""
        now = datetime.now(tz=UTC)
        row_id = uuid.uuid4()

        ep_data = ServiceCatalogEndpointData(
            id=uuid.uuid4(),
            service_id=row_id,
            role="main",
            scope="public",
            address="manager.example.com",
            port=443,
            protocol="https",
            metadata={},
        )

        data = ServiceCatalogData(
            id=row_id,
            service_group="manager",
            instance_id="mgr-001",
            display_name="Manager Instance 1",
            version="26.3.0",
            labels={"region": "us-east-1"},
            status=ServiceCatalogStatus.HEALTHY,
            startup_time=now,
            registered_at=now,
            last_heartbeat=now,
            config_hash="abc123",
            endpoints=[ep_data],
        )

        gql = ServiceCatalogGQL.from_data(data)

        assert gql.id == str(row_id)
        assert gql.service_group == "manager"
        assert gql.instance_id == "mgr-001"
        assert gql.display_name == "Manager Instance 1"
        assert gql.version == "26.3.0"
        assert gql.labels == {"region": "us-east-1"}
        assert gql.status == ServiceCatalogStatusGQL.HEALTHY
        assert gql.startup_time == now
        assert gql.registered_at == now
        assert gql.last_heartbeat == now
        assert gql.config_hash == "abc123"
        assert len(gql.endpoints) == 1
        assert gql.endpoints[0].role == "main"

    def test_from_data_no_endpoints(self) -> None:
        """from_data should handle data with no endpoints."""
        now = datetime.now(tz=UTC)

        data = ServiceCatalogData(
            id=uuid.uuid4(),
            service_group="agent",
            instance_id="agent-001",
            display_name="Agent 1",
            version="26.3.0",
            labels={},
            status=ServiceCatalogStatus.UNHEALTHY,
            startup_time=now,
            registered_at=now,
            last_heartbeat=now,
            config_hash="",
            endpoints=[],
        )

        gql = ServiceCatalogGQL.from_data(data)

        assert gql.endpoints == []
        assert gql.status == ServiceCatalogStatusGQL.UNHEALTHY


class TestServiceCatalogFilterGQL:
    """Tests for ServiceCatalogFilterGQL filter conditions."""

    def test_build_conditions_empty(self) -> None:
        """Empty filter should produce no conditions."""
        f = ServiceCatalogFilterGQL()
        conditions = f.build_conditions()
        assert conditions == []

    def test_build_conditions_service_group(self) -> None:
        """Filter by service_group should produce one condition."""
        f = ServiceCatalogFilterGQL(service_group="manager")
        conditions = f.build_conditions()
        assert len(conditions) == 1
        assert str(conditions[0]().compile(compile_kwargs={"literal_binds": True}))

    def test_build_conditions_status(self) -> None:
        """Filter by status should produce one condition."""
        f = ServiceCatalogFilterGQL(status=ServiceCatalogStatusGQL.HEALTHY)
        conditions = f.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_combined(self) -> None:
        """Filter with both fields should produce two conditions."""
        f = ServiceCatalogFilterGQL(
            service_group="agent",
            status=ServiceCatalogStatusGQL.DEREGISTERED,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

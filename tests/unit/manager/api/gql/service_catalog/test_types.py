"""Unit tests for service catalog GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.service_catalog.types import (
    ServiceCatalogEndpointGQL,
    ServiceCatalogFilterGQL,
    ServiceCatalogGQL,
    ServiceCatalogStatusGQL,
)
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
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

    def test_from_row(self) -> None:
        """from_row should correctly map all endpoint fields."""
        row = MagicMock(spec=ServiceCatalogEndpointRow)
        row.role = "main"
        row.scope = "private"
        row.address = "10.0.0.1"
        row.port = 8080
        row.protocol = "grpc"
        row.metadata_ = {"key": "value"}

        endpoint = ServiceCatalogEndpointGQL.from_row(row)

        assert endpoint.role == "main"
        assert endpoint.scope == "private"
        assert endpoint.address == "10.0.0.1"
        assert endpoint.port == 8080
        assert endpoint.protocol == "grpc"
        assert endpoint.metadata == {"key": "value"}

    def test_from_row_null_metadata(self) -> None:
        """from_row should handle None metadata."""
        row = MagicMock(spec=ServiceCatalogEndpointRow)
        row.role = "health"
        row.scope = "internal"
        row.address = "127.0.0.1"
        row.port = 8081
        row.protocol = "http"
        row.metadata_ = None

        endpoint = ServiceCatalogEndpointGQL.from_row(row)

        assert endpoint.metadata is None


class TestServiceCatalogGQL:
    """Tests for ServiceCatalogGQL type."""

    def test_from_row(self) -> None:
        """from_row should correctly map all catalog fields including nested endpoints."""
        now = datetime.now(tz=UTC)
        row_id = uuid.uuid4()

        ep_row = MagicMock(spec=ServiceCatalogEndpointRow)
        ep_row.role = "main"
        ep_row.scope = "public"
        ep_row.address = "manager.example.com"
        ep_row.port = 443
        ep_row.protocol = "https"
        ep_row.metadata_ = {}

        row = MagicMock(spec=ServiceCatalogRow)
        row.id = row_id
        row.service_group = "manager"
        row.instance_id = "mgr-001"
        row.display_name = "Manager Instance 1"
        row.version = "26.3.0"
        row.labels = {"region": "us-east-1"}
        row.status = ServiceCatalogStatus.HEALTHY
        row.startup_time = now
        row.registered_at = now
        row.last_heartbeat = now
        row.config_hash = "abc123"
        row.endpoints = [ep_row]

        gql = ServiceCatalogGQL.from_row(row)

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

    def test_from_row_no_endpoints(self) -> None:
        """from_row should handle rows with no endpoints."""
        now = datetime.now(tz=UTC)
        row = MagicMock(spec=ServiceCatalogRow)
        row.id = uuid.uuid4()
        row.service_group = "agent"
        row.instance_id = "agent-001"
        row.display_name = "Agent 1"
        row.version = "26.3.0"
        row.labels = {}
        row.status = ServiceCatalogStatus.UNHEALTHY
        row.startup_time = now
        row.registered_at = now
        row.last_heartbeat = now
        row.config_hash = ""
        row.endpoints = []

        gql = ServiceCatalogGQL.from_row(row)

        assert gql.endpoints == []
        assert gql.status == ServiceCatalogStatusGQL.UNHEALTHY


class TestServiceCatalogFilterGQL:
    """Tests for ServiceCatalogFilterGQL filter conditions."""

    def test_build_sa_conditions_empty(self) -> None:
        """Empty filter should produce no conditions."""
        f = ServiceCatalogFilterGQL()
        conditions = f.build_sa_conditions()
        assert conditions == []

    def test_build_sa_conditions_service_group(self) -> None:
        """Filter by service_group should produce one condition."""
        f = ServiceCatalogFilterGQL(service_group="manager")
        conditions = f.build_sa_conditions()
        assert len(conditions) == 1
        # Verify the condition compiles (it's a BinaryExpression)
        assert str(conditions[0].compile(compile_kwargs={"literal_binds": True}))

    def test_build_sa_conditions_status(self) -> None:
        """Filter by status should produce one condition."""
        f = ServiceCatalogFilterGQL(status=ServiceCatalogStatusGQL.HEALTHY)
        conditions = f.build_sa_conditions()
        assert len(conditions) == 1

    def test_build_sa_conditions_combined(self) -> None:
        """Filter with both fields should produce two conditions."""
        f = ServiceCatalogFilterGQL(
            service_group="agent",
            status=ServiceCatalogStatusGQL.DEREGISTERED,
        )
        conditions = f.build_sa_conditions()
        assert len(conditions) == 2

"""Unit tests for service catalog GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogFilter as ServiceCatalogFilterDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import ServiceCatalogNode
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
    ServiceCatalogStatus,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.service_catalog.types import (
    ServiceCatalogEndpointGQL,
    ServiceCatalogFilterGQL,
    ServiceCatalogGQL,
    ServiceCatalogStatusFilterGQL,
    ServiceCatalogStatusGQL,
)


class TestServiceCatalogStatusGQL:
    """Tests for ServiceCatalogStatusGQL enum value alignment with ServiceCatalogStatus."""

    def test_healthy_value_matches(self) -> None:
        assert ServiceCatalogStatus.HEALTHY.value == ServiceCatalogStatusGQL.HEALTHY.value

    def test_unhealthy_value_matches(self) -> None:
        assert ServiceCatalogStatus.UNHEALTHY.value == ServiceCatalogStatusGQL.UNHEALTHY.value

    def test_deregistered_value_matches(self) -> None:
        assert ServiceCatalogStatus.DEREGISTERED.value == ServiceCatalogStatusGQL.DEREGISTERED.value


class TestServiceCatalogEndpointGQL:
    """Tests for ServiceCatalogEndpointGQL type."""

    def test_from_pydantic(self) -> None:
        """from_pydantic should correctly map all endpoint fields."""
        info = EndpointInfo(
            id=uuid.uuid4(),
            role="main",
            scope="private",
            address="10.0.0.1",
            port=8080,
            protocol="grpc",
            metadata={"key": "value"},
        )

        endpoint = ServiceCatalogEndpointGQL.from_pydantic(info)

        assert endpoint.role == "main"
        assert endpoint.scope == "private"
        assert endpoint.address == "10.0.0.1"
        assert endpoint.port == 8080
        assert endpoint.protocol == "grpc"
        assert cast(dict[str, Any], endpoint.metadata) == {"key": "value"}

    def test_from_pydantic_null_metadata(self) -> None:
        """from_pydantic should handle None metadata."""
        info = EndpointInfo(
            id=uuid.uuid4(),
            role="health",
            scope="internal",
            address="127.0.0.1",
            port=8081,
            protocol="http",
            metadata=None,
        )

        endpoint = ServiceCatalogEndpointGQL.from_pydantic(info)

        assert endpoint.metadata is None


class TestServiceCatalogGQL:
    """Tests for ServiceCatalogGQL type."""

    def test_from_pydantic(self) -> None:
        """from_pydantic should correctly map all catalog fields including nested endpoints."""
        now = datetime.now(tz=UTC)
        row_id = uuid.uuid4()

        ep_info = EndpointInfo(
            id=uuid.uuid4(),
            role="main",
            scope="public",
            address="manager.example.com",
            port=443,
            protocol="https",
            metadata={},
        )

        node = ServiceCatalogNode(
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
            endpoints=[ep_info],
        )

        gql = ServiceCatalogGQL.from_pydantic(node)

        assert gql.id == str(row_id)
        assert gql.service_group == "manager"
        assert gql.instance_id == "mgr-001"
        assert gql.display_name == "Manager Instance 1"
        assert gql.version == "26.3.0"
        assert cast(dict[str, Any], gql.labels) == {"region": "us-east-1"}
        assert gql.status == ServiceCatalogStatusGQL.HEALTHY
        assert gql.startup_time == now
        assert gql.registered_at == now
        assert gql.last_heartbeat == now
        assert gql.config_hash == "abc123"
        assert len(gql.endpoints) == 1
        assert gql.endpoints[0].role == "main"

    def test_from_pydantic_no_endpoints(self) -> None:
        """from_pydantic should handle data with no endpoints."""
        now = datetime.now(tz=UTC)

        node = ServiceCatalogNode(
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

        gql = ServiceCatalogGQL.from_pydantic(node)

        assert gql.endpoints == []
        assert gql.status == ServiceCatalogStatusGQL.UNHEALTHY


class TestServiceCatalogFilterGQL:
    """Tests for ServiceCatalogFilterGQL.to_pydantic() conversion."""

    def test_to_pydantic_empty(self) -> None:
        """Empty filter should produce a DTO with all None fields."""
        f = ServiceCatalogFilterGQL()
        dto = f.to_pydantic()
        assert isinstance(dto, ServiceCatalogFilterDTO)
        assert dto.service_group is None
        assert dto.status is None

    def test_to_pydantic_service_group(self) -> None:
        """Filter by service_group should produce DTO with service_group set."""
        f = ServiceCatalogFilterGQL(service_group=StringFilter(equals="manager"))
        dto = f.to_pydantic()
        assert isinstance(dto, ServiceCatalogFilterDTO)
        assert dto.service_group is not None
        assert dto.service_group.equals == "manager"

    def test_to_pydantic_status(self) -> None:
        """Filter by status should produce DTO with status set."""
        f = ServiceCatalogFilterGQL(
            status=ServiceCatalogStatusFilterGQL(equals=ServiceCatalogStatusGQL.HEALTHY)
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ServiceCatalogFilterDTO)
        assert dto.status is not None

    def test_to_pydantic_combined(self) -> None:
        """Filter with both fields should produce DTO with both fields set."""
        f = ServiceCatalogFilterGQL(
            service_group=StringFilter(equals="agent"),
            status=ServiceCatalogStatusFilterGQL(equals=ServiceCatalogStatusGQL.DEREGISTERED),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ServiceCatalogFilterDTO)
        assert dto.service_group is not None
        assert dto.service_group.equals == "agent"
        assert dto.status is not None

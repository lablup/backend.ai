"""GraphQL types for service catalog."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)

__all__ = (
    "ServiceCatalogEndpointGQL",
    "ServiceCatalogFilterGQL",
    "ServiceCatalogGQL",
    "ServiceCatalogStatusGQL",
)


@strawberry.enum(
    name="ServiceCatalogStatus",
    description="Added in 26.3.0. Health status of a service in the catalog.",
)
class ServiceCatalogStatusGQL(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEREGISTERED = "deregistered"

    @classmethod
    def from_status(cls, status: ServiceCatalogStatus) -> ServiceCatalogStatusGQL:
        match status:
            case ServiceCatalogStatus.HEALTHY:
                return cls.HEALTHY
            case ServiceCatalogStatus.UNHEALTHY:
                return cls.UNHEALTHY
            case ServiceCatalogStatus.DEREGISTERED:
                return cls.DEREGISTERED


@strawberry.type(
    name="ServiceCatalogEndpoint",
    description="Added in 26.3.0. An endpoint exposed by a service instance.",
)
class ServiceCatalogEndpointGQL:
    role: str = strawberry.field(description="Role of this endpoint (e.g., 'main', 'health').")
    scope: str = strawberry.field(
        description="Network scope (e.g., 'public', 'private', 'internal')."
    )
    address: str = strawberry.field(description="Hostname or IP address.")
    port: int = strawberry.field(description="Port number.")
    protocol: str = strawberry.field(description="Protocol (e.g., 'grpc', 'http', 'https').")
    metadata: JSON | None = strawberry.field(description="Additional metadata.", default=None)

    @classmethod
    def from_row(cls, row: ServiceCatalogEndpointRow) -> Self:
        return cls(
            role=row.role,
            scope=row.scope,
            address=row.address,
            port=row.port,
            protocol=row.protocol,
            metadata=row.metadata_,
        )


@strawberry.type(
    name="ServiceCatalog",
    description="Added in 26.3.0. A registered service instance in the catalog.",
)
class ServiceCatalogGQL(Node):
    id: NodeID[str] = strawberry.field(description="Relay-style global node ID.")
    service_group: str = strawberry.field(
        description=dedent_strip("""
            Logical group name (e.g., 'manager', 'agent', 'storage-proxy').
        """)
    )
    instance_id: str = strawberry.field(description="Unique instance identifier within the group.")
    display_name: str = strawberry.field(description="Human-readable display name.")
    version: str = strawberry.field(description="Version of the service instance.")
    labels: JSON = strawberry.field(description="Labels for categorization and filtering.")
    status: ServiceCatalogStatusGQL = strawberry.field(description="Health status of the service.")
    startup_time: datetime = strawberry.field(description="When the service instance started.")
    registered_at: datetime = strawberry.field(description="When the service was first registered.")
    last_heartbeat: datetime = strawberry.field(description="Last heartbeat timestamp.")
    config_hash: str = strawberry.field(description="Hash of the service configuration.")
    endpoints: list[ServiceCatalogEndpointGQL] = strawberry.field(
        description="Endpoints exposed by this service instance."
    )

    @classmethod
    def from_row(cls, row: ServiceCatalogRow) -> Self:
        return cls(
            id=str(row.id),
            service_group=row.service_group,
            instance_id=row.instance_id,
            display_name=row.display_name,
            version=row.version,
            labels=row.labels,
            status=ServiceCatalogStatusGQL.from_status(row.status),
            startup_time=row.startup_time,
            registered_at=row.registered_at,
            last_heartbeat=row.last_heartbeat,
            config_hash=row.config_hash,
            endpoints=[ServiceCatalogEndpointGQL.from_row(ep) for ep in row.endpoints],
        )


@strawberry.input(
    name="ServiceCatalogFilter",
    description="Added in 26.3.0. Filter for service catalog queries.",
)
class ServiceCatalogFilterGQL:
    service_group: str | None = strawberry.field(
        default=None,
        description="Filter by service group name (exact match).",
    )
    status: ServiceCatalogStatusGQL | None = strawberry.field(
        default=None,
        description="Filter by health status.",
    )

    def build_sa_conditions(self) -> list[Any]:
        """Build SQLAlchemy WHERE conditions from filter fields."""
        conditions: list[Any] = []
        if self.service_group is not None:
            conditions.append(ServiceCatalogRow.service_group == self.service_group)
        if self.status is not None:
            conditions.append(ServiceCatalogRow.status == ServiceCatalogStatus(self.status.value))
        return conditions

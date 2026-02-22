"""GraphQL types for service catalog."""

from __future__ import annotations

import enum
from datetime import datetime
from enum import StrEnum
from typing import Self

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = (
    "ServiceCatalogEndpointGQL",
    "ServiceCatalogFilterGQL",
    "ServiceCatalogGQL",
    "ServiceCatalogOrderByGQL",
    "ServiceCatalogOrderFieldGQL",
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
    def from_data(cls, data: ServiceCatalogEndpointData) -> Self:
        return cls(
            role=data.role,
            scope=data.scope,
            address=data.address,
            port=data.port,
            protocol=data.protocol,
            metadata=data.metadata,
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
    def from_data(cls, data: ServiceCatalogData) -> Self:
        return cls(
            id=str(data.id),
            service_group=data.service_group,
            instance_id=data.instance_id,
            display_name=data.display_name,
            version=data.version,
            labels=data.labels,
            status=ServiceCatalogStatusGQL.from_status(data.status),
            startup_time=data.startup_time,
            registered_at=data.registered_at,
            last_heartbeat=data.last_heartbeat,
            config_hash=data.config_hash,
            endpoints=[ServiceCatalogEndpointGQL.from_data(ep) for ep in data.endpoints],
        )


@strawberry.enum(
    name="ServiceCatalogOrderField",
    description="Added in 26.3.0. Fields available for ordering service catalog queries.",
)
class ServiceCatalogOrderFieldGQL(enum.Enum):
    SERVICE_GROUP = "SERVICE_GROUP"
    REGISTERED_AT = "REGISTERED_AT"


@strawberry.input(
    name="ServiceCatalogOrderBy",
    description="Added in 26.3.0. Specifies the field and direction for ordering service catalog queries.",
)
class ServiceCatalogOrderByGQL(GQLOrderBy):
    field: ServiceCatalogOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ServiceCatalogOrderFieldGQL.SERVICE_GROUP:
                order = ServiceCatalogRow.service_group
            case ServiceCatalogOrderFieldGQL.REGISTERED_AT:
                order = ServiceCatalogRow.registered_at
        return order.asc() if ascending else order.desc()


@strawberry.input(
    name="ServiceCatalogFilter",
    description="Added in 26.3.0. Filter for service catalog queries.",
)
class ServiceCatalogFilterGQL(GQLFilter):
    service_group: str | None = strawberry.field(
        default=None,
        description="Filter by service group name (exact match).",
    )
    status: ServiceCatalogStatusGQL | None = strawberry.field(
        default=None,
        description="Filter by health status.",
    )

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from filter fields."""
        conditions: list[QueryCondition] = []
        if self.service_group is not None:
            group = self.service_group
            conditions.append(lambda: ServiceCatalogRow.service_group == group)
        if self.status is not None:
            status_val = ServiceCatalogStatus(self.status.value)
            conditions.append(lambda: ServiceCatalogRow.status == status_val)
        return conditions

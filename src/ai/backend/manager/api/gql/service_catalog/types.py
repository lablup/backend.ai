"""GraphQL types for service catalog."""

from __future__ import annotations

import enum
from datetime import datetime
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry.relay import NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogFilter as ServiceCatalogFilterDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogOrder as ServiceCatalogOrderDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    OrderDirection as DtoOrderDirection,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogOrderField as ServiceCatalogOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogStatusFilter as ServiceCatalogStatusFilterDTO,
)
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)

__all__ = (
    "ServiceCatalogEndpointGQL",
    "ServiceCatalogFilterGQL",
    "ServiceCatalogGQL",
    "ServiceCatalogOrderByGQL",
    "ServiceCatalogOrderFieldGQL",
    "ServiceCatalogStatusFilterGQL",
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

    @classmethod
    def from_enum(cls, value: ServiceCatalogStatus) -> ServiceCatalogStatusGQL:
        return cls.from_status(value)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="An endpoint exposed by a service instance.",
    ),
    name="ServiceCatalogEndpoint",
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

    @classmethod
    def from_pydantic(cls, info: EndpointInfo) -> Self:
        """Convert an EndpointInfo Pydantic DTO to this GQL type."""
        return cls(
            role=info.role,
            scope=info.scope,
            address=info.address,
            port=info.port,
            protocol=info.protocol,
            metadata=info.metadata,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="A registered service instance in the catalog.",
    ),
    name="ServiceCatalog",
)
class ServiceCatalogGQL(PydanticNodeMixin[Any]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies the field and direction for ordering service catalog queries.",
        added_version="26.3.0",
    ),
    model=ServiceCatalogOrderDTO,
    name="ServiceCatalogOrderBy",
)
class ServiceCatalogOrderByGQL:
    field: ServiceCatalogOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ServiceCatalogOrderDTO:
        return ServiceCatalogOrderDTO(
            field=ServiceCatalogOrderFieldDTO[self.field.name],
            direction=DtoOrderDirection(self.direction.value),
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for ServiceCatalogStatus enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.3.0",
    ),
    model=ServiceCatalogStatusFilterDTO,
    name="ServiceCatalogStatusFilter",
)
class ServiceCatalogStatusFilterGQL:
    """Filter for service catalog status enum fields."""

    equals: ServiceCatalogStatusGQL | None = strawberry.field(
        default=None,
        description="Exact match for service catalog status.",
    )
    in_: list[ServiceCatalogStatusGQL] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided statuses.",
    )
    not_equals: ServiceCatalogStatusGQL | None = strawberry.field(
        default=None,
        description="Exclude exact status match.",
    )
    not_in: list[ServiceCatalogStatusGQL] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided statuses.",
    )

    def to_pydantic(self) -> ServiceCatalogStatusFilterDTO:
        return ServiceCatalogStatusFilterDTO(
            equals=ServiceCatalogStatus(self.equals.value) if self.equals is not None else None,
            in_=(
                [ServiceCatalogStatus(s.value) for s in self.in_] if self.in_ is not None else None
            ),
            not_equals=(
                ServiceCatalogStatus(self.not_equals.value) if self.not_equals is not None else None
            ),
            not_in=(
                [ServiceCatalogStatus(s.value) for s in self.not_in]
                if self.not_in is not None
                else None
            ),
        )


@strawberry.input(
    name="ServiceCatalogFilter",
    description="Added in 26.3.0. Filter for service catalog queries.",
)
class ServiceCatalogFilterGQL:
    service_group: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by service group name. Supports equals, contains, startsWith, and endsWith.",
    )
    status: ServiceCatalogStatusFilterGQL | None = strawberry.field(
        default=None,
        description="Filter by health status. Supports equals, in, not_equals, and not_in operations.",
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> ServiceCatalogFilterDTO:
        return ServiceCatalogFilterDTO(
            service_group=(
                self.service_group.to_pydantic() if self.service_group is not None else None
            ),
            status=self.status.to_pydantic() if self.status is not None else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )

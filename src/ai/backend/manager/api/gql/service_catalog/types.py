"""GraphQL types for service catalog."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

import strawberry
from strawberry.relay import NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogFilter as ServiceCatalogFilterDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogOrder as ServiceCatalogOrderDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import ServiceCatalogNode
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogStatusFilter as ServiceCatalogStatusFilterDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.utils import dedent_strip

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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="An endpoint exposed by a service instance.",
    ),
    model=EndpointInfo,
    name="ServiceCatalogEndpoint",
)
class ServiceCatalogEndpointGQL(PydanticOutputMixin[EndpointInfo]):
    role: str = strawberry.field(description="Role of this endpoint (e.g., 'main', 'health').")
    scope: str = strawberry.field(
        description="Network scope (e.g., 'public', 'private', 'internal')."
    )
    address: str = strawberry.field(description="Hostname or IP address.")
    port: int = strawberry.field(description="Port number.")
    protocol: str = strawberry.field(description="Protocol (e.g., 'grpc', 'http', 'https').")
    metadata: JSON | None = strawberry.field(description="Additional metadata.", default=None)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="A registered service instance in the catalog.",
    ),
    name="ServiceCatalog",
)
class ServiceCatalogGQL(PydanticNodeMixin[ServiceCatalogNode]):
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


@strawberry.enum(
    name="ServiceCatalogOrderField",
    description="Added in 26.3.0. Fields available for ordering service catalog queries.",
)
class ServiceCatalogOrderFieldGQL(StrEnum):
    SERVICE_GROUP = "service_group"
    REGISTERED_AT = "registered_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies the field and direction for ordering service catalog queries.",
        added_version="26.3.0",
    ),
    name="ServiceCatalogOrderBy",
)
class ServiceCatalogOrderByGQL(PydanticInputMixin[ServiceCatalogOrderDTO]):
    field: ServiceCatalogOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for ServiceCatalogStatus enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.3.0",
    ),
    name="ServiceCatalogStatusFilter",
)
class ServiceCatalogStatusFilterGQL(PydanticInputMixin[ServiceCatalogStatusFilterDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for service catalog queries.", added_version="26.3.0"),
    name="ServiceCatalogFilter",
)
class ServiceCatalogFilterGQL(PydanticInputMixin[ServiceCatalogFilterDTO]):
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

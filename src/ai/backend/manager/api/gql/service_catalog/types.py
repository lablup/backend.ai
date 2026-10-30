"""GraphQL types for service catalog."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import NodeID
from strawberry.scalars import JSON

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogFilter as ServiceCatalogFilterDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    ServiceCatalogOrder as ServiceCatalogOrderDTO,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import ServiceCatalogNode
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogStatusFilter as ServiceCatalogStatusFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
)
from ai.backend.manager.api.gql.storage_volume_service_attachment.types import (
    StorageVolumeServiceAttachmentConnectionGQL,
    StorageVolumeServiceAttachmentFilterGQL,
    StorageVolumeServiceAttachmentOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "ServiceCatalogFilterGQL",
    "ServiceCatalogGQL",
    "ServiceCatalogOrderByGQL",
    "ServiceCatalogOrderFieldGQL",
    "ServiceCatalogStatusFilterGQL",
    "ServiceCatalogStatusGQL",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Health status of a service in the catalog."
    ),
    name="ServiceCatalogStatus",
)
class ServiceCatalogStatusGQL(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEREGISTERED = "deregistered"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="A registered service instance in the catalog.",
    ),
    name="ServiceCatalog",
)
class ServiceCatalogGQL(PydanticNodeMixin[ServiceCatalogNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node ID.")
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.9.0",
            description="UUID of the service catalog.",
        ),
    )
    service_group: str = gql_field(
        description="Logical group name (e.g., 'manager', 'agent', 'storage-proxy')."
    )
    instance_id: str = gql_field(description="Unique instance identifier within the group.")
    display_name: str = gql_field(description="Human-readable display name.")
    version: str = gql_field(description="Version of the service instance.")
    labels: JSON = gql_field(description="Labels for categorization and filtering.")
    status: ServiceCatalogStatusGQL = gql_field(description="Health status of the service.")
    startup_time: datetime = gql_field(description="When the service instance started.")
    registered_at: datetime = gql_field(description="When the service was first registered.")
    last_heartbeat: datetime = gql_field(description="Last heartbeat timestamp.")
    config_hash: str = gql_field(description="Hash of the service configuration.")

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The storage volumes attached to this service, one attachment per volume.",
        )
    )  # type: ignore[misc]
    async def storage_volume_attachments(
        self,
        info: Info[StrawberryGQLContext],
        filter: StorageVolumeServiceAttachmentFilterGQL | None = None,
        order_by: list[StorageVolumeServiceAttachmentOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> StorageVolumeServiceAttachmentConnectionGQL | None:
        raise NotImplementedError

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[ServiceCatalogGQL | None]:
        return await info.context.data_loaders.service_catalog_loader.load_many([
            ServiceCatalogID(UUID(nid)) for nid in node_ids
        ])


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering service catalog queries.",
    ),
    name="ServiceCatalogOrderField",
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

    equals: ServiceCatalogStatusGQL | None = gql_field(
        description="Exact match for service catalog status.", default=None
    )
    in_: list[ServiceCatalogStatusGQL] | None = gql_field(
        description="Match any of the provided statuses.", name="in", default=None
    )
    not_equals: ServiceCatalogStatusGQL | None = gql_field(
        description="Exclude exact status match.", default=None
    )
    not_in: list[ServiceCatalogStatusGQL] | None = gql_field(
        description="Exclude any of the provided statuses.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for service catalog queries.", added_version="26.3.0"),
    name="ServiceCatalogFilter",
)
class ServiceCatalogFilterGQL(PydanticInputMixin[ServiceCatalogFilterDTO]):
    service_group: StringFilter | None = gql_field(
        description="Filter by service group name. Supports equals, contains, startsWith, and endsWith.",
        default=None,
    )
    status: ServiceCatalogStatusFilterGQL | None = gql_field(
        description="Filter by health status. Supports equals, in, not_equals, and not_in operations.",
        default=None,
    )
    entity_id: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter by service ID."),
        default=None,
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

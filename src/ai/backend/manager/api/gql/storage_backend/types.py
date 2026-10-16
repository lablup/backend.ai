"""Storage backend GQL node, connection, filter, input and payload types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, override
from uuid import UUID

from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.storage_backend.request import (
    ServiceStorageBackendStatusFilter as ServiceStorageBackendStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.request import (
    ServiceStorageBackendStatusOrder as ServiceStorageBackendStatusOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.request import (
    StorageBackendFilter as StorageBackendFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.request import (
    StorageBackendOrder as StorageBackendOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.request import (
    UpdateStorageBackendInput as UpdateStorageBackendInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    DeleteStorageBackendPayload as DeleteStorageBackendPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    PurgeStorageBackendPayload as PurgeStorageBackendPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    RestoreStorageBackendPayload as RestoreStorageBackendPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    SearchServiceStorageBackendStatusesPayload as SearchServiceStorageBackendStatusesPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    ServiceStorageBackendStatusNode,
    StorageBackendNode,
)
from ai.backend.common.dto.manager.v2.storage_backend.response import (
    UpdateStorageBackendPayload as UpdateStorageBackendPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "DeleteStorageBackendPayloadGQL",
    "StorageBackendEdgeGQL",
    "PurgeStorageBackendPayloadGQL",
    "RestoreStorageBackendPayloadGQL",
    "UpdateStorageBackendPayloadGQL",
    "ServiceStorageBackendStatusGQL",
    "ServiceStorageBackendStatusListGQL",
    "ServiceStorageBackendStatusOrderByGQL",
    "StorageBackendConnectionGQL",
    "StorageBackendEdgeGQL",
    "StorageBackendFilterGQL",
    "StorageBackendGQL",
    "StorageBackendOrderByGQL",
    "UpdateStorageBackendInputGQL",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A storage backend as one service last reported it.",
    ),
    model=ServiceStorageBackendStatusNode,
    name="ServiceStorageBackendStatus",
)
class ServiceStorageBackendStatusGQL(PydanticOutputMixin[ServiceStorageBackendStatusNode]):
    service_catalog_id: UUID = gql_field(description="ID of the reporting service.")
    storage_backend_id: UUID = gql_field(description="ID of the reported storage backend.")
    status_checked_at: datetime | None = gql_field(
        description="When the reporting service last checked the backend."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A page of the per-service status rows. Paged by limit and offset: a status"
            " row carries no id of its own to put in a cursor."
        ),
    ),
    model=SearchServiceStorageBackendStatusesPayloadDTO,
    name="ServiceStorageBackendStatusList",
)
class ServiceStorageBackendStatusListGQL(
    PydanticOutputMixin[SearchServiceStorageBackendStatusesPayloadDTO]
):
    items: list[ServiceStorageBackendStatusGQL] = gql_field(description="The status rows read.")
    total_count: int = gql_field(description="Total number of matching status rows.")
    has_next_page: bool = gql_field(description="Whether more rows follow this page.")
    has_previous_page: bool = gql_field(description="Whether more rows precede this page.")


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering the per-service status rows.",
    ),
    name="ServiceStorageBackendStatusOrderField",
)
class ServiceStorageBackendStatusOrderFieldGQL(StrEnum):
    SERVICE_CATALOG_ID = "service_catalog_id"
    STORAGE_BACKEND_ID = "storage_backend_id"
    STATUS_CHECKED_AT = "status_checked_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for the per-service status rows.",
    ),
    name="ServiceStorageBackendStatusOrderBy",
)
class ServiceStorageBackendStatusOrderByGQL(
    PydanticInputMixin[ServiceStorageBackendStatusOrderDTO]
):
    field: ServiceStorageBackendStatusOrderFieldGQL = gql_field(
        description="The field to order by."
    )
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the per-service status rows of the backends.",
    ),
    name="ServiceStorageBackendStatusFilter",
)
class ServiceStorageBackendStatusFilterGQL(
    PydanticInputMixin[ServiceStorageBackendStatusFilterDTO]
):
    service_catalog_id: UUIDFilter | None = gql_field(
        description="Filter by the reporting service's ID.", default=None
    )
    storage_backend_id: UUIDFilter | None = gql_field(
        description="Filter by the reported backend's ID.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given filters.", default=None)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A storage appliance a service can reach. How it is reached is the holding"
            " service's own configuration and is never returned."
        ),
    ),
    name="StorageBackend",
)
class StorageBackendGQL(PydanticNodeMixin[StorageBackendNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node ID.")
    entity_id: UUID = gql_field(description="UUID of the storage backend.")
    name: str = gql_field(description="Storage backend name.")
    storage_backend_type_id: UUID = gql_field(
        description="ID of the backend implementation serving this appliance."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @gql_field(description="What the services report about this backend, one row per service.")  # type: ignore[misc]
    async def service_statuses(
        self,
        info: Info[StrawberryGQLContext],
        filter: ServiceStorageBackendStatusFilterGQL | None = None,
        order_by: list[ServiceStorageBackendStatusOrderByGQL] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ServiceStorageBackendStatusListGQL | None:
        raise NotImplementedError

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[StorageBackendGQL | None]:
        raise NotImplementedError


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One storage backend within a connection.",
    ),
    name="StorageBackendEdge",
)
class StorageBackendEdgeGQL(Edge[StorageBackendGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for storage backends.",
    ),
    name="StorageBackendConnection",
)
class StorageBackendConnectionGQL(Connection[StorageBackendGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[StorageBackendEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of storage backends matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering storage backends.",
    ),
    name="StorageBackendOrderField",
)
class StorageBackendOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for storage backend queries.",
    ),
    name="StorageBackendOrderBy",
)
class StorageBackendOrderByGQL(PydanticInputMixin[StorageBackendOrderDTO]):
    field: StorageBackendOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for storage backend queries.",
    ),
    name="StorageBackendFilter",
)
class StorageBackendFilterGQL(PydanticInputMixin[StorageBackendFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(description="Filter by backend ID.", default=None)
    name: StringFilter | None = gql_field(description="Filter by backend name.", default=None)
    storage_backend_type_id: UUIDFilter | None = gql_field(
        description="Filter by the backend implementation's ID.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating the metadata an administrator owns on a backend.",
    ),
    name="UpdateStorageBackendInput",
)
class UpdateStorageBackendInputGQL(PydanticInputMixin[UpdateStorageBackendInputDTO]):
    name: str | None = gql_field(description="Updated backend name.", default=UNSET)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after purging a storage backend.",
    ),
    model=PurgeStorageBackendPayloadDTO,
    name="PurgeStorageBackendPayload",
)
class PurgeStorageBackendPayloadGQL(PydanticOutputMixin[PurgeStorageBackendPayloadDTO]):
    id: UUID = gql_field(description="ID of the purged storage backend.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after updating a storage backend.",
    ),
    model=UpdateStorageBackendPayloadDTO,
    name="UpdateStorageBackendPayload",
)
class UpdateStorageBackendPayloadGQL(PydanticOutputMixin[UpdateStorageBackendPayloadDTO]):
    item: StorageBackendGQL = gql_field(description="The updated storage backend.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after withdrawing a storage backend from new use.",
    ),
    model=DeleteStorageBackendPayloadDTO,
    name="DeleteStorageBackendPayload",
)
class DeleteStorageBackendPayloadGQL(PydanticOutputMixin[DeleteStorageBackendPayloadDTO]):
    id: UUID = gql_field(description="ID of the withdrawn storage backend.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after restoring a withdrawn storage backend.",
    ),
    model=RestoreStorageBackendPayloadDTO,
    name="RestoreStorageBackendPayload",
)
class RestoreStorageBackendPayloadGQL(PydanticOutputMixin[RestoreStorageBackendPayloadDTO]):
    id: UUID = gql_field(description="ID of the restored storage backend.")

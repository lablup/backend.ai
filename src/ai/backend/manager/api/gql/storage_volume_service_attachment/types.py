"""Storage volume service attachment GQL node, connection, filter and order types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceAttachmentFilter as StorageVolumeServiceAttachmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceAttachmentOrder as StorageVolumeServiceAttachmentOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    StorageVolumeServiceAttachmentNode,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    StorageVolumeServiceAttachmentOrderField as StorageVolumeServiceAttachmentOrderFieldDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import NullableDateTimeFilter, OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.storage_volume.types import StorageVolumeFilterGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.service_catalog.types import (
        ServiceCatalogFilterGQL,
        ServiceCatalogGQL,
    )
    from ai.backend.manager.api.gql.storage_volume.types import StorageVolumeGQL

__all__ = (
    "StorageVolumeServiceAttachmentConnectionGQL",
    "StorageVolumeServiceAttachmentEdgeGQL",
    "StorageVolumeServiceAttachmentFilterGQL",
    "StorageVolumeServiceAttachmentGQL",
    "StorageVolumeServiceAttachmentOrderByGQL",
)


StorageVolumeServiceAttachmentOrderFieldGQL: type[StorageVolumeServiceAttachmentOrderFieldDTO] = (
    gql_enum(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Fields available for ordering the storage volume service attachments.",
        ),
        StorageVolumeServiceAttachmentOrderFieldDTO,
        name="StorageVolumeServiceAttachmentOrderField",
    )
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for the storage volume service attachments.",
    ),
    name="StorageVolumeServiceAttachmentOrderBy",
)
class StorageVolumeServiceAttachmentOrderByGQL(
    PydanticInputMixin[StorageVolumeServiceAttachmentOrderDTO]
):
    field: StorageVolumeServiceAttachmentOrderFieldGQL = gql_field(
        description="The field to order by."
    )
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the storage volume service attachments.",
    ),
    name="StorageVolumeServiceAttachmentFilter",
)
class StorageVolumeServiceAttachmentFilterGQL(
    PydanticInputMixin[StorageVolumeServiceAttachmentFilterDTO]
):
    status_checked_at: NullableDateTimeFilter | None = gql_field(
        description="Filter by when the service last checked the volume.", default=None
    )
    storage_volume: StorageVolumeFilterGQL | None = gql_field(
        description="Filter by conditions on the attached volume.", default=None
    )
    service_catalog: (
        Annotated[
            ServiceCatalogFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.service_catalog.types"),
        ]
        | None
    ) = gql_field(
        description="Filter by conditions on the service the volume is attached to.",
        default=None,
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
        description="A storage volume as one service has it attached.",
    ),
    name="StorageVolumeServiceAttachment",
)
class StorageVolumeServiceAttachmentGQL(PydanticNodeMixin[StorageVolumeServiceAttachmentNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node ID, built from the service and the volume IDs."
    )
    service_catalog_id: UUID = gql_field(description="ID of the service the volume is attached to.")
    storage_volume_id: UUID = gql_field(description="ID of the attached volume.")
    status_checked_at: datetime | None = gql_field(
        description="When the service last checked the volume. Null until the first check."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @gql_field(description="The attached volume.")  # type: ignore[misc]
    async def storage_volume(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[
        StorageVolumeGQL,
        strawberry.lazy("ai.backend.manager.api.gql.storage_volume.types"),
    ]:
        raise NotImplementedError

    @gql_field(description="The service the volume is attached to.")  # type: ignore[misc]
    async def service_catalog(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[
        ServiceCatalogGQL,
        strawberry.lazy("ai.backend.manager.api.gql.service_catalog.types"),
    ]:
        raise NotImplementedError

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[StorageVolumeServiceAttachmentGQL | None]:
        raise NotImplementedError


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One storage volume service attachment within a connection.",
    ),
    name="StorageVolumeServiceAttachmentEdge",
)
class StorageVolumeServiceAttachmentEdgeGQL(Edge[StorageVolumeServiceAttachmentGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for storage volume service attachments.",
    ),
    name="StorageVolumeServiceAttachmentConnection",
)
class StorageVolumeServiceAttachmentConnectionGQL(Connection[StorageVolumeServiceAttachmentGQL]):
    edges: list[StorageVolumeServiceAttachmentEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(
        description="Total number of storage volume service attachments matching the query."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count

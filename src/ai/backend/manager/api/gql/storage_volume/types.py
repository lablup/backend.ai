"""Storage volume GQL node, connection, filter, input and payload types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, override
from uuid import UUID

from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.storage_volume.request import (
    PurgeResourceGroupVolumeOfferInput as PurgeResourceGroupVolumeOfferInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    ResourceGroupVolumeOfferFilter as ResourceGroupVolumeOfferFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    ResourceGroupVolumeOfferOrder as ResourceGroupVolumeOfferOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeFilter as StorageVolumeFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeOrder as StorageVolumeOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceHoldingFilter as StorageVolumeServiceHoldingFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceHoldingOrder as StorageVolumeServiceHoldingOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    UpdateStorageVolumeInput as UpdateStorageVolumeInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    UpsertResourceGroupVolumeOfferInput as UpsertResourceGroupVolumeOfferInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    DeleteStorageVolumePayload as DeleteStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    PurgeResourceGroupVolumeOfferPayload as PurgeResourceGroupVolumeOfferPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    PurgeStorageVolumePayload as PurgeStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    ResourceGroupVolumeOfferNode,
    StorageVolumeNode,
    StorageVolumeServiceHoldingNode,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    RestoreStorageVolumePayload as RestoreStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    SearchResourceGroupVolumeOffersPayload as SearchResourceGroupVolumeOffersPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    SearchStorageVolumeServiceHoldingsPayload as SearchStorageVolumeServiceHoldingsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    UpdateStorageVolumePayload as UpdateStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    UpsertResourceGroupVolumeOfferPayload as UpsertResourceGroupVolumeOfferPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    StorageVolumeUsageExposureInfo,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    StorageVolumeUsageExposureInput as StorageVolumeUsageExposureInputDTO,
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
    "DeleteStorageVolumePayloadGQL",
    "StorageVolumeEdgeGQL",
    "PurgeResourceGroupVolumeOfferInputGQL",
    "PurgeResourceGroupVolumeOfferPayloadGQL",
    "PurgeStorageVolumePayloadGQL",
    "RestoreStorageVolumePayloadGQL",
    "UpsertResourceGroupVolumeOfferInputGQL",
    "UpsertResourceGroupVolumeOfferPayloadGQL",
    "UpdateStorageVolumePayloadGQL",
    "ResourceGroupVolumeOfferFilterGQL",
    "ResourceGroupVolumeOfferGQL",
    "ResourceGroupVolumeOfferListGQL",
    "ResourceGroupVolumeOfferOrderByGQL",
    "StorageVolumeConnectionGQL",
    "StorageVolumeEdgeGQL",
    "StorageVolumeFilterGQL",
    "StorageVolumeGQL",
    "StorageVolumeOrderByGQL",
    "StorageVolumeServiceHoldingFilterGQL",
    "StorageVolumeServiceHoldingGQL",
    "StorageVolumeServiceHoldingListGQL",
    "StorageVolumeServiceHoldingOrderByGQL",
    "StorageVolumeUsageFieldGQL",
    "UpdateStorageVolumeInputGQL",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A usage figure a volume may show a user.",
    ),
    name="StorageVolumeUsageField",
)
class StorageVolumeUsageFieldGQL(StrEnum):
    PERCENTAGE = "percentage"
    USED_BYTES = "used_bytes"
    CAPACITY_BYTES = "capacity_bytes"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Which usage figures a volume shows a user.",
    ),
    model=StorageVolumeUsageExposureInfo,
    name="StorageVolumeUsageExposure",
)
class StorageVolumeUsageExposureGQL(PydanticOutputMixin[StorageVolumeUsageExposureInfo]):
    exposed: list[StorageVolumeUsageFieldGQL] = gql_field(
        description="The usage figures the volume shows."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for which usage figures a volume shows a user.",
    ),
    name="StorageVolumeUsageExposureInput",
)
class StorageVolumeUsageExposureInputGQL(PydanticInputMixin[StorageVolumeUsageExposureInputDTO]):
    exposed: list[StorageVolumeUsageFieldGQL] = gql_field(
        description="The usage figures the volume shows. Replaces the whole set."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A storage volume as one service holds it.",
    ),
    model=StorageVolumeServiceHoldingNode,
    name="StorageVolumeServiceHolding",
)
class StorageVolumeServiceHoldingGQL(PydanticOutputMixin[StorageVolumeServiceHoldingNode]):
    service_catalog_id: UUID = gql_field(description="ID of the holding service.")
    storage_volume_id: UUID = gql_field(description="ID of the held volume.")
    status_checked_at: datetime | None = gql_field(
        description="When the holding service last checked the volume."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A page of the per-service holdings. Paged by limit and offset: a holding"
            " carries no id of its own to put in a cursor."
        ),
    ),
    model=SearchStorageVolumeServiceHoldingsPayloadDTO,
    name="StorageVolumeServiceHoldingList",
)
class StorageVolumeServiceHoldingListGQL(
    PydanticOutputMixin[SearchStorageVolumeServiceHoldingsPayloadDTO]
):
    items: list[StorageVolumeServiceHoldingGQL] = gql_field(description="The holdings read.")
    total_count: int = gql_field(description="Total number of matching holdings.")
    has_next_page: bool = gql_field(description="Whether more rows follow this page.")
    has_previous_page: bool = gql_field(description="Whether more rows precede this page.")


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering the per-service holdings.",
    ),
    name="StorageVolumeServiceHoldingOrderField",
)
class StorageVolumeServiceHoldingOrderFieldGQL(StrEnum):
    SERVICE_CATALOG_ID = "service_catalog_id"
    STORAGE_VOLUME_ID = "storage_volume_id"
    STATUS_CHECKED_AT = "status_checked_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for the per-service holdings.",
    ),
    name="StorageVolumeServiceHoldingOrderBy",
)
class StorageVolumeServiceHoldingOrderByGQL(
    PydanticInputMixin[StorageVolumeServiceHoldingOrderDTO]
):
    field: StorageVolumeServiceHoldingOrderFieldGQL = gql_field(
        description="The field to order by."
    )
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the per-service holdings of the volumes.",
    ),
    name="StorageVolumeServiceHoldingFilter",
)
class StorageVolumeServiceHoldingFilterGQL(
    PydanticInputMixin[StorageVolumeServiceHoldingFilterDTO]
):
    service_catalog_id: UUIDFilter | None = gql_field(
        description="Filter by the holding service's ID.", default=None
    )
    storage_volume_id: UUIDFilter | None = gql_field(
        description="Filter by the held volume's ID.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given filters.", default=None)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A storage volume offered to a resource group.",
    ),
    model=ResourceGroupVolumeOfferNode,
    name="ResourceGroupVolumeOffer",
)
class ResourceGroupVolumeOfferGQL(PydanticOutputMixin[ResourceGroupVolumeOfferNode]):
    resource_group_id: UUID = gql_field(description="ID of the resource group offered to.")
    storage_volume_id: UUID = gql_field(description="ID of the offered volume.")
    enabled: bool = gql_field(description="Whether the offer is enabled.")
    is_default: bool = gql_field(description="Whether the offer is the resource group's default.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A page of the offers to resource groups. Paged by limit and offset: an offer"
            " carries no id of its own to put in a cursor."
        ),
    ),
    model=SearchResourceGroupVolumeOffersPayloadDTO,
    name="ResourceGroupVolumeOfferList",
)
class ResourceGroupVolumeOfferListGQL(
    PydanticOutputMixin[SearchResourceGroupVolumeOffersPayloadDTO]
):
    items: list[ResourceGroupVolumeOfferGQL] = gql_field(description="The offers read.")
    total_count: int = gql_field(description="Total number of matching offers.")
    has_next_page: bool = gql_field(description="Whether more rows follow this page.")
    has_previous_page: bool = gql_field(description="Whether more rows precede this page.")


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering the offers to resource groups.",
    ),
    name="ResourceGroupVolumeOfferOrderField",
)
class ResourceGroupVolumeOfferOrderFieldGQL(StrEnum):
    RESOURCE_GROUP_ID = "resource_group_id"
    STORAGE_VOLUME_ID = "storage_volume_id"
    IS_DEFAULT = "is_default"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for the offers to resource groups.",
    ),
    name="ResourceGroupVolumeOfferOrderBy",
)
class ResourceGroupVolumeOfferOrderByGQL(PydanticInputMixin[ResourceGroupVolumeOfferOrderDTO]):
    field: ResourceGroupVolumeOfferOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the offers of the volumes to resource groups.",
    ),
    name="ResourceGroupVolumeOfferFilter",
)
class ResourceGroupVolumeOfferFilterGQL(PydanticInputMixin[ResourceGroupVolumeOfferFilterDTO]):
    resource_group_id: UUIDFilter | None = gql_field(
        description="Filter by the resource group offered to.", default=None
    )
    storage_volume_id: UUIDFilter | None = gql_field(
        description="Filter by the offered volume's ID.", default=None
    )
    enabled: bool | None = gql_field(
        description="Filter by whether the offer is enabled.", default=None
    )
    is_default: bool | None = gql_field(
        description="Filter by whether the offer is the resource group's default.", default=None
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
            "A volume on a storage backend, identified by the name every service declares it under."
        ),
    ),
    name="StorageVolumeV2",
)
class StorageVolumeGQL(PydanticNodeMixin[StorageVolumeNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node ID.")
    entity_id: UUID = gql_field(description="UUID of the storage volume.")
    name: str = gql_field(description="Volume name, as every service declares it.")
    storage_backend_id: UUID = gql_field(description="ID of the backend the volume sits on.")
    status_stale_after_seconds: int = gql_field(
        description=("How long the volume may go without a fresh check before it counts as stale.")
    )
    usage_exposure: StorageVolumeUsageExposureGQL = gql_field(
        description="Which usage figures the volume shows a user."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @gql_field(description="Which services hold this volume, one row per service.")  # type: ignore[misc]
    async def service_holdings(
        self,
        info: Info[StrawberryGQLContext],
        filter: StorageVolumeServiceHoldingFilterGQL | None = None,
        order_by: list[StorageVolumeServiceHoldingOrderByGQL] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> StorageVolumeServiceHoldingListGQL | None:
        raise NotImplementedError

    @gql_field(description="Which resource groups this volume is offered to.")  # type: ignore[misc]
    async def resource_group_offers(
        self,
        info: Info[StrawberryGQLContext],
        filter: ResourceGroupVolumeOfferFilterGQL | None = None,
        order_by: list[ResourceGroupVolumeOfferOrderByGQL] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ResourceGroupVolumeOfferListGQL | None:
        raise NotImplementedError

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[StorageVolumeGQL | None]:
        raise NotImplementedError


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One storage volume within a connection.",
    ),
    name="StorageVolumeV2Edge",
)
class StorageVolumeEdgeGQL(Edge[StorageVolumeGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for storage volumes.",
    ),
    name="StorageVolumeV2Connection",
)
class StorageVolumeConnectionGQL(Connection[StorageVolumeGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[StorageVolumeEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of storage volumes matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering storage volumes.",
    ),
    name="StorageVolumeOrderField",
)
class StorageVolumeOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for storage volume queries.",
    ),
    name="StorageVolumeOrderBy",
)
class StorageVolumeOrderByGQL(PydanticInputMixin[StorageVolumeOrderDTO]):
    field: StorageVolumeOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for storage volume queries.",
    ),
    name="StorageVolumeFilter",
)
class StorageVolumeFilterGQL(PydanticInputMixin[StorageVolumeFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(description="Filter by volume ID.", default=None)
    name: StringFilter | None = gql_field(description="Filter by volume name.", default=None)
    storage_backend_id: UUIDFilter | None = gql_field(
        description="Filter by the backend the volume sits on.", default=None
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
        description="Input for updating the metadata an administrator owns on a volume.",
    ),
    name="UpdateStorageVolumeInput",
)
class UpdateStorageVolumeInputGQL(PydanticInputMixin[UpdateStorageVolumeInputDTO]):
    name: str | None = gql_field(description="Updated volume name.", default=UNSET)
    status_stale_after_seconds: int | None = gql_field(
        description="Updated stale threshold, in seconds.", default=UNSET
    )
    usage_exposure: StorageVolumeUsageExposureInputGQL | None = gql_field(
        description="Updated usage exposure.", default=UNSET
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after purging a storage volume.",
    ),
    model=PurgeStorageVolumePayloadDTO,
    name="PurgeStorageVolumePayload",
)
class PurgeStorageVolumePayloadGQL(PydanticOutputMixin[PurgeStorageVolumePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged storage volume.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after updating a storage volume.",
    ),
    model=UpdateStorageVolumePayloadDTO,
    name="UpdateStorageVolumePayload",
)
class UpdateStorageVolumePayloadGQL(PydanticOutputMixin[UpdateStorageVolumePayloadDTO]):
    item: StorageVolumeGQL = gql_field(description="The updated storage volume.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for offering a volume to a resource group, or for retuning an offer."
            " The pair is the key, so offering a volume already offered rewrites the flags"
            " it carries."
        ),
    ),
    name="UpsertResourceGroupVolumeOfferInput",
)
class UpsertResourceGroupVolumeOfferInputGQL(
    PydanticInputMixin[UpsertResourceGroupVolumeOfferInputDTO]
):
    resource_group_id: UUID = gql_field(description="The resource group the volume is offered to.")
    storage_volume_id: UUID = gql_field(description="The volume being offered.")
    enabled: bool | None = gql_field(
        description="Whether the offer is enabled. Defaults to true on a new offer.",
        default=UNSET,
    )
    is_default: bool | None = gql_field(
        description=(
            "Whether the offer is the resource group's default. Defaults to false on a new"
            " offer. At most one offer per resource group may be the default."
        ),
        default=UNSET,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after offering a volume to a resource group.",
    ),
    model=UpsertResourceGroupVolumeOfferPayloadDTO,
    name="UpsertResourceGroupVolumeOfferPayload",
)
class UpsertResourceGroupVolumeOfferPayloadGQL(
    PydanticOutputMixin[UpsertResourceGroupVolumeOfferPayloadDTO]
):
    item: ResourceGroupVolumeOfferGQL = gql_field(description="The offer written.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for withdrawing a volume from a resource group.",
    ),
    name="PurgeResourceGroupVolumeOfferInput",
)
class PurgeResourceGroupVolumeOfferInputGQL(
    PydanticInputMixin[PurgeResourceGroupVolumeOfferInputDTO]
):
    resource_group_id: UUID = gql_field(description="The resource group the volume was offered to.")
    storage_volume_id: UUID = gql_field(description="The volume being withdrawn.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after withdrawing a volume from a resource group.",
    ),
    model=PurgeResourceGroupVolumeOfferPayloadDTO,
    name="PurgeResourceGroupVolumeOfferPayload",
)
class PurgeResourceGroupVolumeOfferPayloadGQL(
    PydanticOutputMixin[PurgeResourceGroupVolumeOfferPayloadDTO]
):
    resource_group_id: UUID = gql_field(description="The resource group the volume was offered to.")
    storage_volume_id: UUID = gql_field(description="The volume withdrawn.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after withdrawing a storage volume from new use.",
    ),
    model=DeleteStorageVolumePayloadDTO,
    name="DeleteStorageVolumePayload",
)
class DeleteStorageVolumePayloadGQL(PydanticOutputMixin[DeleteStorageVolumePayloadDTO]):
    id: UUID = gql_field(description="ID of the withdrawn storage volume.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after restoring a withdrawn storage volume.",
    ),
    model=RestoreStorageVolumePayloadDTO,
    name="RestoreStorageVolumePayload",
)
class RestoreStorageVolumePayloadGQL(PydanticOutputMixin[RestoreStorageVolumePayloadDTO]):
    id: UUID = gql_field(description="ID of the restored storage volume.")

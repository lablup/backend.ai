"""Storage volume GQL query and mutation resolvers."""

from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.storage_volume.types import (
    DeleteStorageVolumePayloadGQL,
    PurgeResourceGroupVolumeOfferInputGQL,
    PurgeResourceGroupVolumeOfferPayloadGQL,
    PurgeStorageVolumePayloadGQL,
    RestoreStorageVolumePayloadGQL,
    StorageVolumeConnectionGQL,
    StorageVolumeFilterGQL,
    StorageVolumeGQL,
    StorageVolumeOrderByGQL,
    UpdateStorageVolumeInputGQL,
    UpdateStorageVolumePayloadGQL,
    UpsertResourceGroupVolumeOfferInputGQL,
    UpsertResourceGroupVolumeOfferPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "delete_storage_volume",
    "purge_resource_group_volume_offer",
    "purge_storage_volume",
    "restore_storage_volume",
    "storage_volume",
    "storage_volumes",
    "update_storage_volume",
    "upsert_resource_group_volume_offer",
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read one storage volume.",
    )
)  # type: ignore[misc]
async def storage_volume(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> StorageVolumeGQL | None:
    raise NotImplementedError


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Page through the declared storage volumes.",
    )
)  # type: ignore[misc]
async def storage_volumes(
    info: Info[StrawberryGQLContext],
    filter: StorageVolumeFilterGQL | None = None,
    order_by: list[StorageVolumeOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> StorageVolumeConnectionGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Retune one storage volume: its name, its usage exposure and its stale threshold."
        ),
    )
)
async def update_storage_volume(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: UpdateStorageVolumeInputGQL,
) -> UpdateStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Remove one storage volume from the catalog. Refused while a folder sits on"
            " it or a resource group is offered it."
        ),
    )
)
async def purge_storage_volume(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> PurgeStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Offer one volume to one resource group, or retune the offer. Offering a volume"
            " already offered rewrites the flags it carries."
        ),
    )
)
async def upsert_resource_group_volume_offer(
    info: Info[StrawberryGQLContext],
    input: UpsertResourceGroupVolumeOfferInputGQL,
) -> UpsertResourceGroupVolumeOfferPayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Withdraw one volume from one resource group. The volume and the folders on it"
            " stay; only the offer goes."
        ),
    )
)
async def purge_resource_group_volume_offer(
    info: Info[StrawberryGQLContext],
    input: PurgeResourceGroupVolumeOfferInputGQL,
) -> PurgeResourceGroupVolumeOfferPayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Withhold one storage volume from new use. The folders already on it keep"
            " working and the volume still answers get and search."
        ),
    )
)
async def delete_storage_volume(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Take one withdrawn storage volume back into use.",
    )
)
async def restore_storage_volume(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> RestoreStorageVolumePayloadGQL | None:
    raise NotImplementedError

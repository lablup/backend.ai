"""Storage volume GQL query and mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.storage_volume.types import (
    DeleteStorageVolumePayloadGQL,
    PurgeStorageVolumePayloadGQL,
    RestoreStorageVolumePayloadGQL,
    StorageVolumeConnectionGQL,
    StorageVolumeFilterGQL,
    StorageVolumeGQL,
    StorageVolumeOrderByGQL,
    UpdateStorageVolumeInputGQL,
    UpdateStorageVolumePayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "admin_storage_volumes",
    "delete_storage_volume",
    "purge_storage_volume",
    "restore_storage_volume",
    "storage_volume",
    "update_storage_volume",
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read one storage volume.",
    )
)  # type: ignore[misc]
async def storage_volume(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> StorageVolumeGQL | None:
    raise NotImplementedError


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Page through every declared storage volume. Admin only.",
    )
)  # type: ignore[misc]
async def admin_storage_volumes(
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
    id: UUID,
    input: UpdateStorageVolumeInputGQL,
) -> UpdateStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Remove one storage volume from the catalog. Refused while a folder sits on it."
        ),
    )
)
async def purge_storage_volume(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Soft-delete one storage volume, withholding it from new use. The folders already"
            " on it keep working. A get still answers it; a search lists it only when the"
            " filter gives deletedAt."
        ),
    )
)
async def delete_storage_volume(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteStorageVolumePayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore one soft-deleted storage volume back into use.",
    )
)
async def restore_storage_volume(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RestoreStorageVolumePayloadGQL | None:
    raise NotImplementedError

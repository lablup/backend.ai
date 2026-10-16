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
    PurgeStorageVolumePayloadGQL,
    RestoreStorageVolumePayloadGQL,
    StorageVolumeConnectionGQL,
    StorageVolumeFilterGQL,
    StorageVolumeGQL,
    StorageVolumeOrderByGQL,
    StorageVolumeScopeGQL,
    UpdateStorageVolumeInputGQL,
    UpdateStorageVolumePayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "admin_storage_volumes",
    "delete_storage_volume",
    "purge_storage_volume",
    "restore_storage_volume",
    "scoped_storage_volumes",
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
    id: ID,
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the storage volumes the named scopes reach, combined with OR."
            " Every scope is authorized before the read runs."
        ),
    )
)  # type: ignore[misc]
async def scoped_storage_volumes(
    info: Info[StrawberryGQLContext],
    scope: StorageVolumeScopeGQL,
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
            "Remove one storage volume from the catalog. Refused while a folder sits on it."
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

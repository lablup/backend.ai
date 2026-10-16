"""Storage backend GQL query and mutation resolvers."""

from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.storage_backend.types import (
    DeleteStorageBackendPayloadGQL,
    PurgeStorageBackendPayloadGQL,
    RestoreStorageBackendPayloadGQL,
    StorageBackendConnectionGQL,
    StorageBackendFilterGQL,
    StorageBackendGQL,
    StorageBackendOrderByGQL,
    UpdateStorageBackendInputGQL,
    UpdateStorageBackendPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "admin_delete_storage_backend",
    "admin_purge_storage_backend",
    "admin_restore_storage_backend",
    "admin_storage_backend",
    "admin_storage_backends",
    "admin_update_storage_backend",
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read one storage backend. Admin only.",
    )
)  # type: ignore[misc]
async def admin_storage_backend(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> StorageBackendGQL | None:
    raise NotImplementedError


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Page through the registered storage backends. Admin only.",
    )
)  # type: ignore[misc]
async def admin_storage_backends(
    info: Info[StrawberryGQLContext],
    filter: StorageBackendFilterGQL | None = None,
    order_by: list[StorageBackendOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> StorageBackendConnectionGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Rename one storage backend. Admin only.",
    )
)
async def admin_update_storage_backend(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: UpdateStorageBackendInputGQL,
) -> UpdateStorageBackendPayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Remove one storage backend from the catalog. Refused while a volume still"
            " sits on it. Admin only."
        ),
    )
)
async def admin_purge_storage_backend(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> PurgeStorageBackendPayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Withhold one storage backend from new use. The volumes already on it keep"
            " working and the backend still answers get and search. Admin only."
        ),
    )
)
async def admin_delete_storage_backend(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteStorageBackendPayloadGQL | None:
    raise NotImplementedError


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Take one withdrawn storage backend back into use. Admin only.",
    )
)
async def admin_restore_storage_backend(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> RestoreStorageBackendPayloadGQL | None:
    raise NotImplementedError

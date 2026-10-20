"""Storage volume service attachment GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.storage_volume_service_attachment.types import (
    StorageVolumeServiceAttachmentConnectionGQL,
    StorageVolumeServiceAttachmentFilterGQL,
    StorageVolumeServiceAttachmentOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = ("admin_storage_volume_service_attachments",)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Page through every storage volume service attachment. Admin only.",
    )
)  # type: ignore[misc]
async def admin_storage_volume_service_attachments(
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

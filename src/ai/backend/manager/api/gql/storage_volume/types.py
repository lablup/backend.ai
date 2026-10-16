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
    StorageVolumeFilter as StorageVolumeFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeOrder as StorageVolumeOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeScope,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceAttachmentFilter as StorageVolumeServiceAttachmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    StorageVolumeServiceAttachmentOrder as StorageVolumeServiceAttachmentOrderDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    UpdateStorageVolumeInput as UpdateStorageVolumeInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    DeleteStorageVolumePayload as DeleteStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    PurgeStorageVolumePayload as PurgeStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    RestoreStorageVolumePayload as RestoreStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    StorageVolumeNode,
    StorageVolumeServiceAttachmentNode,
)
from ai.backend.common.dto.manager.v2.storage_volume.response import (
    UpdateStorageVolumePayload as UpdateStorageVolumePayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    StorageVolumeUsageExposureInfo,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    StorageVolumeUsageExposureInput as StorageVolumeUsageExposureInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    UUIDFilter,
    UUIDScopeGQL,
)
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
    "PurgeStorageVolumePayloadGQL",
    "RestoreStorageVolumePayloadGQL",
    "StorageVolumeConnectionGQL",
    "StorageVolumeEdgeGQL",
    "StorageVolumeFilterGQL",
    "StorageVolumeGQL",
    "StorageVolumeOrderByGQL",
    "StorageVolumeScopeGQL",
    "StorageVolumeServiceAttachmentConnectionGQL",
    "StorageVolumeServiceAttachmentEdgeGQL",
    "StorageVolumeServiceAttachmentFilterGQL",
    "StorageVolumeServiceAttachmentGQL",
    "StorageVolumeServiceAttachmentOrderByGQL",
    "StorageVolumeUsageFieldGQL",
    "UpdateStorageVolumeInputGQL",
    "UpdateStorageVolumePayloadGQL",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "The scopes a storage volume read is answered for. Each list is OR'd internally"
            " and across lists, and every scope named is authorized before the read runs."
        ),
    ),
    name="StorageVolumeScope",
)
class StorageVolumeScopeGQL(PydanticInputMixin[StorageVolumeScope]):
    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose storage volumes are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose storage volumes are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users whose storage volumes are being read."
    )
    storage_backend: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Storage backends whose volumes are being read."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A storage volume as one service has it attached. The volume and the service are"
            " the attachment's immutable identity."
        ),
    ),
    name="StorageVolumeServiceAttachment",
)
class StorageVolumeServiceAttachmentGQL(PydanticNodeMixin[StorageVolumeServiceAttachmentNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node ID.")
    service_catalog_id: UUID = gql_field(description="ID of the service the volume is attached to.")
    storage_volume_id: UUID = gql_field(description="ID of the attached volume.")
    status_checked_at: datetime | None = gql_field(
        description="When the service last checked the volume."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

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
        description="Paginated connection for the storage volume service attachments.",
    ),
    name="StorageVolumeServiceAttachmentConnection",
)
class StorageVolumeServiceAttachmentConnectionGQL(Connection[StorageVolumeServiceAttachmentGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[StorageVolumeServiceAttachmentEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(
        description="Total number of storage volume service attachments matching the query."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering the storage volume service attachments.",
    ),
    name="StorageVolumeServiceAttachmentOrderField",
)
class StorageVolumeServiceAttachmentOrderFieldGQL(StrEnum):
    SERVICE_CATALOG_ID = "service_catalog_id"
    STORAGE_VOLUME_ID = "storage_volume_id"
    STATUS_CHECKED_AT = "status_checked_at"
    UPDATED_AT = "updated_at"


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
    service_catalog_id: UUIDFilter | None = gql_field(
        description="Filter by the service the volume is attached to.", default=None
    )
    storage_volume_id: UUIDFilter | None = gql_field(
        description="Filter by the attached volume's ID.", default=None
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

    @gql_field(  # type: ignore[misc]
        description="Which services have this volume attached, one row per service."
    )
    async def service_attachments(
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after withdrawing a storage volume from new use.",
    ),
    model=DeleteStorageVolumePayloadDTO,
    name="DeleteStorageVolumePayload",
)
class DeleteStorageVolumePayloadGQL(PydanticOutputMixin[DeleteStorageVolumePayloadDTO]):
    item: StorageVolumeGQL = gql_field(description="The withdrawn storage volume.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after restoring a withdrawn storage volume.",
    ),
    model=RestoreStorageVolumePayloadDTO,
    name="RestoreStorageVolumePayload",
)
class RestoreStorageVolumePayloadGQL(PydanticOutputMixin[RestoreStorageVolumePayloadDTO]):
    item: StorageVolumeGQL = gql_field(description="The restored storage volume.")

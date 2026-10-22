"""
Request DTOs for Storage Volume DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    NullableDateTimeFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import String64
from ai.backend.common.dto.manager.v2.service_catalog.request import ServiceCatalogFilter
from ai.backend.common.tristate.unset import UNSET, Unset

from .types import (
    OrderDirection,
    StorageVolumeOrderField,
    StorageVolumeServiceAttachmentOrderField,
    StorageVolumeUsageExposureInput,
)

__all__ = (
    "AdminSearchStorageVolumeServiceAttachmentsInput",
    "AdminSearchStorageVolumesInput",
    "StorageVolumeFilter",
    "StorageVolumeOrder",
    "StorageVolumeServiceAttachmentFilter",
    "StorageVolumeServiceAttachmentOrder",
    "UpdateStorageVolumeInput",
)


class StorageVolumeFilter(BaseRequestModel):
    """Filter conditions for a storage volume search.

    Volumes marked deleted are left out unless the top-level filter gives ``deleted_at``.
    A ``deleted_at`` inside ``AND``/``OR``/``NOT`` does not lift that default.
    """

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by volume ID.")
    name: StringFilter | None = Field(default=None, description="Filter by volume name.")
    storage_backend_id: UUIDFilter | None = Field(
        default=None, description="Filter by the backend the volume sits on."
    )
    deleted_at: NullableDateTimeFilter | None = Field(
        default=None,
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the volumes"
            " marked deleted; inside AND, OR or NOT it does not."
        ),
    )
    AND: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[StorageVolumeFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


StorageVolumeFilter.model_rebuild()


class StorageVolumeOrder(BaseRequestModel):
    """Order specification for a storage volume search."""

    field: StorageVolumeOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchStorageVolumesInput(BaseRequestModel):
    """Input for an administrator's storage volume search over the whole system.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: StorageVolumeFilter | None = Field(default=None, description="Filter conditions.")
    order: list[StorageVolumeOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class UpdateStorageVolumeInput(BaseRequestModel):
    """Input for updating the metadata an administrator owns on a volume."""

    name: String64 | None | Unset = Field(
        default=UNSET,
        description="Updated volume name. Omit to leave unchanged.",
    )
    status_stale_after_seconds: int | None | Unset = Field(
        default=UNSET,
        ge=1,
        description=(
            "How long the volume may go without a fresh check before it counts as stale."
            " Omit to leave unchanged."
        ),
    )
    usage_exposure: StorageVolumeUsageExposureInput | None | Unset = Field(
        default=UNSET,
        description="Updated usage exposure. Omit to leave unchanged.",
    )


class StorageVolumeServiceAttachmentFilter(BaseRequestModel):
    """Filter conditions for the storage volume service attachments."""

    status_checked_at: NullableDateTimeFilter | None = Field(
        default=None, description="Filter by when the service last checked the volume."
    )
    storage_volume: StorageVolumeFilter | None = Field(
        default=None, description="Filter by conditions on the attached volume."
    )
    service_catalog: ServiceCatalogFilter | None = Field(
        default=None, description="Filter by conditions on the service the volume is attached to."
    )
    AND: list[StorageVolumeServiceAttachmentFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[StorageVolumeServiceAttachmentFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[StorageVolumeServiceAttachmentFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


StorageVolumeServiceAttachmentFilter.model_rebuild()


class StorageVolumeServiceAttachmentOrder(BaseRequestModel):
    """Order specification for the storage volume service attachments."""

    field: StorageVolumeServiceAttachmentOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchStorageVolumeServiceAttachmentsInput(BaseRequestModel):
    """Input for an administrator's search over every storage volume service attachment.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: StorageVolumeServiceAttachmentFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[StorageVolumeServiceAttachmentOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")

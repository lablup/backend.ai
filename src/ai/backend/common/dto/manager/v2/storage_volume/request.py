"""
Request DTOs for Storage Volume DTO v2.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import String64
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.tristate.unset import UNSET, Unset

from .types import (
    OrderDirection,
    StorageVolumeOrderField,
    StorageVolumeUsageExposureInput,
)

__all__ = (
    "AdminSearchStorageVolumesInput",
    "ScopedSearchStorageVolumesInput",
    "StorageVolumeFilter",
    "StorageVolumeOrder",
    "StorageVolumeScope",
    "UpdateStorageVolumeInput",
)


class StorageVolumeFilter(BaseRequestModel):
    """Filter conditions for a storage volume search."""

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by volume ID.")
    name: StringFilter | None = Field(default=None, description="Filter by volume name.")
    storage_backend_id: UUIDFilter | None = Field(
        default=None, description="Filter by the backend the volume sits on."
    )
    enabled: bool | None = Field(default=None, description="Filter by the enabled flag.")
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


class StorageVolumeScope(BaseRequestModel):
    """Scope for a storage volume search.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose storage volumes are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose storage volumes are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose storage volumes are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> StorageVolumeScope:
        if not self.domain and not self.project and not self.user:
            raise ValueError(
                "StorageVolumeScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self


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


class ScopedSearchStorageVolumesInput(BaseRequestModel):
    """Input for searching the storage volumes the named scopes reach."""

    scope: StorageVolumeScope = Field(description="Scope (OR across all items).")
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

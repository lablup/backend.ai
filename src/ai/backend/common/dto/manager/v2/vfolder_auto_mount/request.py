"""
Request DTOs for VFolderAutoMount v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    NullableDateTimeFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import (
    VFolderAutoMountOrderField,
    VFolderAutoMountScope,
)
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.common.types import MountPermission

__all__ = (
    "CreateVFolderAutoMountInput",
    "DeleteVFolderAutoMountInput",
    "ScopedSearchVFolderAutoMountsInput",
    "UpdateVFolderAutoMountInput",
    "VFolderAutoMountFilter",
    "VFolderAutoMountOrder",
    "VFolderAutoMountPermissionFilter",
)


class VFolderAutoMountPermissionFilter(EnumFilter[MountPermission]):
    """Filter for the permission a vfolder is auto-mounted with."""


class VFolderAutoMountFilter(BaseRequestModel):
    """Filter for vfolder auto-mounts.

    Auto-mounts marked deleted are left out unless the top-level filter gives ``deleted_at``.
    A ``deleted_at`` inside ``AND``/``OR``/``NOT`` does not lift that default.
    """

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by auto-mount ID.")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID.")
    vfolder_id: UUIDFilter | None = Field(default=None, description="Filter by vfolder ID.")
    mount_destination: StringFilter | None = Field(
        default=None, description="Filter by mount destination."
    )
    mount_permission: VFolderAutoMountPermissionFilter | None = Field(
        default=None, description="Filter by mount permission."
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    updated_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last update time."
    )
    deleted_at: NullableDateTimeFilter | None = Field(
        default=None,
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the "
            "auto-mounts marked deleted; inside AND, OR or NOT it does not."
        ),
    )

    AND: list[VFolderAutoMountFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[VFolderAutoMountFilter] | None = Field(
        default=None, description="OR logical combinator."
    )
    NOT: list[VFolderAutoMountFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


VFolderAutoMountFilter.model_rebuild()


class VFolderAutoMountOrder(BaseRequestModel):
    """Order specification for vfolder auto-mounts."""

    field: VFolderAutoMountOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchVFolderAutoMountsInput(BaseRequestModel):
    """Input for searching vfolder auto-mounts within scopes."""

    scope: VFolderAutoMountScope = Field(description="Scope (OR across all items).")
    filter: VFolderAutoMountFilter | None = Field(default=None, description="Filter conditions.")
    order: list[VFolderAutoMountOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class CreateVFolderAutoMountInput(BaseRequestModel):
    """Input for auto-mounting a vfolder into every session created in a project.

    The vfolder must belong to that project; for a personal project, that is the
    owner's personal vfolders.
    """

    project_id: UUID = Field(description="ID of the project the vfolder is auto-mounted in.")
    vfolder_id: UUID = Field(description="ID of the vfolder to auto-mount.")
    mount_destination: str = Field(
        min_length=1, description="Path in the session container the vfolder is mounted at."
    )
    subpath: str = Field(default=".", description="Path inside the vfolder that is mounted.")
    mount_permission: MountPermission = Field(description="Permission the vfolder is mounted with.")


class UpdateVFolderAutoMountInput(BaseRequestModel):
    """Input for changing where and how an auto-mounted vfolder is mounted.

    At least one of the three fields must be given a value; a null leaves the field unchanged.
    """

    id: UUID = Field(description="ID of the auto-mount to update.")
    mount_destination: str | None | Unset = Field(
        default=UNSET,
        min_length=1,
        description="New path in the session container. Omit to leave unchanged.",
    )
    subpath: str | None | Unset = Field(
        default=UNSET, description="New path inside the vfolder. Omit to leave unchanged."
    )
    mount_permission: MountPermission | None | Unset = Field(
        default=UNSET, description="New mount permission. Omit to leave unchanged."
    )

    @model_validator(mode="after")
    def _require_a_change(self) -> Self:
        if (
            not isinstance(self.mount_destination, str)
            and not isinstance(self.subpath, str)
            and not isinstance(self.mount_permission, MountPermission)
        ):
            raise ValueError(
                "UpdateVFolderAutoMountInput requires 'mount_destination', 'subpath' or "
                "'mount_permission'"
            )
        return self


class DeleteVFolderAutoMountInput(BaseRequestModel):
    """Input for marking a vfolder auto-mount deleted."""

    id: UUID = Field(description="ID of the auto-mount to delete.")

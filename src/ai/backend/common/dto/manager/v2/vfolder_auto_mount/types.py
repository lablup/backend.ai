"""
Common types for VFolderAutoMount DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "VFolderAutoMountOrderField",
    "VFolderAutoMountScope",
    "VFolderAutoMountScopeRef",
    "VFolderAutoMountScopeType",
)


class VFolderAutoMountOrderField(StrEnum):
    """Fields available for ordering vfolder auto-mounts."""

    MOUNT_DESTINATION = "mount_destination"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"


class VFolderAutoMountScopeRef(BaseRequestModel):
    """The one project or user an auto-mount is set on."""

    scope_type: VFolderAutoMountScopeType = Field(description="Kind of the scope.")
    scope_id: UUID = Field(description="ID of the project or the user.")


class VFolderAutoMountScope(BaseRequestModel):
    """Scope for the scoped vfolder auto-mount query; the items are OR'd."""

    project: list[UUIDScope] | None = Field(
        default=None,
        description="Projects whose auto-mounts are being read. A personal project included.",
    )
    user: list[UUIDScope] | None = Field(
        default=None,
        description=(
            "Users whose own auto-mounts are being read; those of a personal project are not."
        ),
    )

    @model_validator(mode="after")
    def _require_a_scope(self) -> Self:
        if not self.project and not self.user:
            raise ValueError("VFolderAutoMountScope requires a non-empty 'project' or 'user'")
        return self

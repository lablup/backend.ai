"""
Common types for VFolderAutoMount DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.exception import InvalidAPIParameters

__all__ = (
    "VFolderAutoMountOrderField",
    "VFolderAutoMountScope",
)


class VFolderAutoMountOrderField(StrEnum):
    """Fields available for ordering vfolder auto-mounts."""

    MOUNT_DESTINATION = "mount_destination"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"


class VFolderAutoMountScope(BaseRequestModel):
    """Scope for the scoped vfolder auto-mount query; the items are OR'd."""

    project: list[UUIDScope] = Field(
        description="Projects whose auto-mounts are being read. A personal project included."
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> VFolderAutoMountScope:
        if not self.project:
            raise InvalidAPIParameters("VFolderAutoMountScope requires a non-empty 'project'")
        return self

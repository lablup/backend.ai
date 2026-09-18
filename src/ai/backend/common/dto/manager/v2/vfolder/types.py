"""
Common types for vfolder DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.field import (
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.dto.manager.query import EnumFilter
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo, OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.types import VFolderUsageMode

__all__ = (
    "FileEntryType",
    "OrderDirection",
    "VFolderInvitationState",
    "VFolderMetadataInfo",
    "VFolderOperationStatusField",
    "VFolderOrderField",
    "VFolderOwnershipInfo",
    "VFolderOwnershipTypeField",
    "VFolderPermissionField",
    "VFolderAccessControlInfo",
    "VFolderQuotaInfo",
    "VFolderStatusFilter",
    "VFolderUsageInfo",
    "VFolderUsageMode",
    "VFolderUsageModeFilter",
)


class FileEntryType(StrEnum):
    """Type of a file entry in a virtual folder."""

    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    SYMLINK = "SYMLINK"


class VFolderOrderField(StrEnum):
    """Fields available for ordering vfolders."""

    NAME = "name"
    CREATED_AT = "created_at"
    STATUS = "status"
    USAGE_MODE = "usage_mode"
    HOST = "host"


class VFolderInvitationState(StrEnum):
    """Virtual folder invitation state."""

    PENDING = "pending"
    CANCELED = "canceled"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class VFolderStatusFilter(EnumFilter[VFolderOperationStatusField]):
    """Filter for vfolder operation status values."""


class VFolderUsageModeFilter(EnumFilter[VFolderUsageMode]):
    """Filter for vfolder usage mode values."""


class VFolderMetadataInfo(BaseResponseModel):
    """Descriptive metadata fields for a virtual folder."""

    name: str
    usage_mode: VFolderUsageMode
    quota_scope_id: str | None
    created_at: datetime
    last_used: datetime | None
    cloneable: bool


class VFolderAccessControlInfo(BaseResponseModel):
    """Access control fields for a virtual folder."""

    permission: VFolderPermissionField | None
    ownership_type: VFolderOwnershipTypeField


class VFolderOwnershipInfo(BaseResponseModel):
    """Ownership context fields for a virtual folder."""

    user_id: UUID | None
    project_id: UUID | None
    creator_id: UUID | None
    creator_email: str | None


class VFolderQuotaInfo(BaseResponseModel):
    """Quota limits configured for a virtual folder."""

    max_size: BinarySizeInfo | None
    max_files: int


class VFolderUsageInfo(BaseResponseModel):
    """Usage statistics for a virtual folder, measured live through the storage proxy."""

    num_files: int
    used_bytes: BinarySizeInfo


class VFolderScope(BaseRequestModel):
    """Scope for the scoped vfolder query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose vfolders are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose vfolders are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose vfolders are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> VFolderScope:
        if not self.domain and not self.project and not self.user:
            raise ValueError(
                "VFolderScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self

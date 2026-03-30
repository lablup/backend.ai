"""
Common types for vfolder DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.field import (
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo, OrderDirection
from ai.backend.common.types import VFolderUsageMode

__all__ = (
    "OrderDirection",
    "VFolderInvitationState",
    "VFolderMetadataInfo",
    "VFolderOperationStatusField",
    "VFolderOrderField",
    "VFolderOwnerInfo",
    "VFolderOwnershipTypeField",
    "VFolderPermissionField",
    "VFolderAccessControlInfo",
    "VFolderStatusFilter",
    "VFolderUsageInfo",
    "VFolderUsageMode",
    "VFolderUsageModeFilter",
)


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


class VFolderStatusFilter(BaseRequestModel):
    """Filter for vfolder operation status values."""

    in_: list[VFolderOperationStatusField] | None = None
    not_in: list[VFolderOperationStatusField] | None = None


class VFolderUsageModeFilter(BaseRequestModel):
    """Filter for vfolder usage mode values."""

    in_: list[VFolderUsageMode] | None = None
    not_in: list[VFolderUsageMode] | None = None


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


class VFolderOwnerInfo(BaseResponseModel):
    """Owner context fields for a virtual folder."""

    user: UUID | None
    group: UUID | None
    creator: str | None


class VFolderUsageInfo(BaseResponseModel):
    """Usage statistics fields for a virtual folder."""

    num_files: int
    used_bytes: BinarySizeInfo
    max_size: BinarySizeInfo | None
    max_files: int

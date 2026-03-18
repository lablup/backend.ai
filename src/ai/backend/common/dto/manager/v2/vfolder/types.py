"""
Common types for vfolder DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.field import (
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.types import VFolderUsageMode

__all__ = (
    "OrderDirection",
    "VFolderBasicInfo",
    "VFolderInvitationState",
    "VFolderOperationStatusField",
    "VFolderOrderField",
    "VFolderOwnerInfo",
    "VFolderOwnershipTypeField",
    "VFolderPermissionField",
    "VFolderPermissionInfo",
    "VFolderUsageInfo",
    "VFolderUsageMode",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


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


class VFolderBasicInfo(BaseResponseModel):
    """Core identity fields for a virtual folder."""

    id: UUID
    name: str
    host: str
    quota_scope_id: str | None
    usage_mode: VFolderUsageMode
    status: VFolderOperationStatusField
    created_at: datetime
    last_used: datetime | None


class VFolderPermissionInfo(BaseResponseModel):
    """Permission and ownership fields for a virtual folder."""

    permission: VFolderPermissionField
    ownership_type: VFolderOwnershipTypeField
    is_owner: bool
    cloneable: bool


class VFolderOwnerInfo(BaseResponseModel):
    """Owner context fields for a virtual folder."""

    user: UUID | None
    group: UUID | None
    creator: str | None


class VFolderUsageInfo(BaseResponseModel):
    """Usage statistics fields for a virtual folder."""

    num_files: int
    used_bytes: int
    max_size: int | None
    max_files: int

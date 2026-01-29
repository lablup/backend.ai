"""CreatorSpec implementations for vfolder repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class VFolderCreatorSpec(CreatorSpec[VFolderRow]):
    """CreatorSpec for VFolder creation.

    Creates a VFolderRow instance for insertion into the database.
    Used with RBACEntityCreator for automatic RBAC association.
    """

    id: uuid.UUID
    name: str
    domain_name: str
    quota_scope_id: str
    host: str
    creator: str
    ownership_type: VFolderOwnershipType
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL
    permission: VFolderMountPermission = VFolderMountPermission.READ_WRITE
    user: uuid.UUID | None = None
    group: uuid.UUID | None = None
    unmanaged_path: str | None = None
    cloneable: bool = False
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def build_row(self) -> VFolderRow:
        return VFolderRow(
            id=self.id,
            name=self.name,
            domain_name=self.domain_name,
            quota_scope_id=QuotaScopeID.parse(self.quota_scope_id),
            usage_mode=self.usage_mode,
            permission=self.permission,
            last_used=None,
            host=self.host,
            creator=self.creator,
            ownership_type=self.ownership_type,
            user=self.user,
            group=self.group,
            unmanaged_path=self.unmanaged_path,
            cloneable=self.cloneable,
            status=self.status,
        )

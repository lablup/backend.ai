"""Insert specs for vfolders."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.vfolder.row import VFolderRow


@dataclass
class VFolderCreator(EntityCreator[VFolderRow, VFolderData]):
    """Creator for a vfolder.

    A vfolder is its own scope and joins the owner its ownership type names — a user
    or a project — which is what the RBAC element reference used to say from the call
    site.
    """

    id: uuid.UUID
    name: str
    domain_name: str
    quota_scope_id: str
    host: str
    creator: str
    creator_id: uuid.UUID
    ownership_type: VFolderOwnershipType
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL
    permission: VFolderMountPermission = VFolderMountPermission.READ_WRITE
    user: uuid.UUID | None = None
    group: uuid.UUID | None = None
    unmanaged_path: str | None = None
    cloneable: bool = False
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def entity_id(self, row: VFolderRow) -> VFolderUUID:
        return VFolderUUID(row.id)

    @override
    def member_of(self, row: VFolderRow) -> Collection[EntityIdentifier]:
        match self.ownership_type:
            case VFolderOwnershipType.USER if self.user is not None:
                return (UserID(self.user),)
            case VFolderOwnershipType.GROUP if self.group is not None:
                return (ProjectID(self.group),)
            case _:
                return ()

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

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
            creator_id=self.creator_id,
            ownership_type=self.ownership_type,
            user=self.user,
            group=self.group,
            unmanaged_path=self.unmanaged_path,
            cloneable=self.cloneable,
            status=self.status,
        )

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()

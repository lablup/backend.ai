from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.types import EntityData, RuntimeEntityID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.manager.data.vfolder.types import VFolderMountPermission


@dataclass(frozen=True)
class VFolderAutoMountSpec:
    vfolder_id: VFolderUUID
    mount_destination: str
    subpath: str
    mount_permission: VFolderMountPermission


@dataclass(frozen=True)
class VFolderAutoMountData(EntityData):
    id: VFolderAutoMountID
    scope: RuntimeEntityID
    vfolder_id: VFolderUUID
    mount_destination: str
    subpath: str
    mount_permission: VFolderMountPermission
    created_at: datetime
    deleted_at: datetime | None

    @override
    def entity_id(self) -> VFolderAutoMountID:
        return self.id

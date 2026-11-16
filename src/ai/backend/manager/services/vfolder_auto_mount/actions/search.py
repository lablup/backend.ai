from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow

__all__ = ("SearchVFolderAutoMountsAction",)


@dataclass(frozen=True)
class SearchVFolderAutoMountsAction(
    ScopedSearchOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Page through the auto-mounts of the named projects and users, combined with OR."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderAutoMountEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_vfolder_auto_mounts"

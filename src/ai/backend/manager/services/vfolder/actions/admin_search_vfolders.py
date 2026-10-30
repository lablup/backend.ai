from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder.row import VFolderRow


@dataclass(frozen=True)
class GlobalSearchVFoldersAction(GlobalSearcherOpsAction[VFolderRow, VFolderData]):
    """Page through vfolders across every scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_vfolders"

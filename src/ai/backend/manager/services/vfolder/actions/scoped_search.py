"""VFolder search over the scopes vfolders are reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder.row import VFolderRow

__all__ = ("ScopedSearchVFoldersAction",)


@dataclass(frozen=True)
class ScopedSearchVFoldersAction(ScopedSearchOpsAction[VFolderRow, VFolderData]):
    """Page through the vfolders the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_vfolders"

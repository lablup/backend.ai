from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.queriers import BulkVFolderAutoMountQuerier
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow

__all__ = ("BulkGetVFolderAutoMountsAction",)


@dataclass
class BulkGetVFolderAutoMountsAction(
    PartialBulkGetEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Read the auto-mounts the caller named, answering for each id."""

    ids: Sequence[VFolderAutoMountID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_vfolder_auto_mounts"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkVFolderAutoMountQuerier:
        return BulkVFolderAutoMountQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

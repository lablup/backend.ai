from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.queriers import BulkVFSStorageQuerier
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class BulkGetVFSStoragesAction(PartialBulkGetEntityOpsAction[VFSStorageRow, VFSStorageData]):
    """Read the VFS storages the caller named, answering for each id."""

    ids: Sequence[VFSStorageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_vfs_storages"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkVFSStorageQuerier:
        return BulkVFSStorageQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

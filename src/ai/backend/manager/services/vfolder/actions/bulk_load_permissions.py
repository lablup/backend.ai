from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass(frozen=True)
class BulkLoadVFolderPermissionsAction(BasePartialBulkAction):
    """Read the permissions the caller holds on each vfolder named."""

    vfolder_ids: Sequence[VFolderUUID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_load_vfolder_permissions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.vfolder_ids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, vfolder_ids=[vid for vid in self.vfolder_ids if vid in allowed])

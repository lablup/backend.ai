from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.models.vfolder.updaters import VFolderAttributeUpdater


@dataclass(frozen=True)
class PartialBulkUpdateVFoldersAction(BasePartialBulkAction):
    """Edit the named vfolders' attributes, answering for each one."""

    updaters: Sequence[VFolderAttributeUpdater]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_vfolders"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.vfolder_id for updater in self.updaters)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.vfolder_id in allowed]
        )

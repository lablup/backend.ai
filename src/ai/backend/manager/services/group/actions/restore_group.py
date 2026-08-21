from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.group.updaters import GroupRestoreUpdater


@dataclass(frozen=True)
class RestoreGroupAction(RestoreSingleEntityOpsAction[GroupRow, GroupData]):
    """Put one retired project back in service."""

    updater: GroupRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_project"

    @override
    def to_updater(self) -> GroupRestoreUpdater:
        return self.updater

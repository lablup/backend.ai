from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.group.updaters import GroupSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteGroupAction(DeleteSingleEntityOpsAction[GroupRow, GroupData]):
    """Retire one project."""

    updater: GroupSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_project"

    @override
    def to_updater(self) -> GroupSoftDeleteUpdater:
        return self.updater

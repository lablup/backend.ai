from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.updaters import SessionGroupUpdater

__all__ = ("UpdateSessionGroupAction",)


@dataclass(frozen=True)
class UpdateSessionGroupAction(UpdateSingleEntityOpsAction[SessionGroupRow, SessionGroupData]):
    """Change a session group's placement policy for the members placed after it."""

    updater: SessionGroupUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_session_group"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.session_group_id

    @override
    def to_updater(self) -> SessionGroupUpdater:
        return self.updater

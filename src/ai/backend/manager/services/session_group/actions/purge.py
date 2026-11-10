from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.purgers import SessionGroupPurger
from ai.backend.manager.models.session_group.row import SessionGroupRow

__all__ = ("PurgeSessionGroupAction",)


@dataclass(frozen=True)
class PurgeSessionGroupAction(PurgeEntityOpsAction[SessionGroupRow, SessionGroupData]):
    """Remove a session group, keeping its member sessions."""

    purger: SessionGroupPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_session_group"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.purger.entity_id()

    @override
    def to_purger(self) -> SessionGroupPurger:
        return self.purger

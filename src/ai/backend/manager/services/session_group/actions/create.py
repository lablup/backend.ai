from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.creators import SessionGroupCreator
from ai.backend.manager.models.session_group.row import SessionGroupRow

__all__ = ("CreateSessionGroupAction",)


@dataclass(frozen=True)
class CreateSessionGroupAction(CreateEntityOpsAction[SessionGroupRow, SessionGroupData]):
    """Create a session group in a project, owned by the caller."""

    creator: SessionGroupCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionGroupEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.creator.project_id,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_session_group"

    @override
    def to_creator(self) -> SessionGroupCreator:
        return self.creator

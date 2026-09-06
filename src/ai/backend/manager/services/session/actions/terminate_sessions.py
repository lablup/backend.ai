from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass
class TerminateSessionsAction(BasePartialBulkAction):
    """Terminate the sessions the caller named.

    Every named session is answered for on its own, which is what the bulk shape
    says, and the answer carries which of the four states it ended in.
    """

    session_ids: list[SessionId]
    forced: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "terminate_sessions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(sid) for sid in self.session_ids]

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            session_ids=[sid for sid in self.session_ids if SessionID(sid) in allowed],
        )

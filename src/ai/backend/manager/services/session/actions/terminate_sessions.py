from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction


@dataclass
class TerminateSessionsAction(BaseBulkAction):
    """Terminate the sessions the caller named.

    Gated atomically: a caller refused any of them is refused the run, so nothing is
    terminated behind a denial. Every named session is still answered for on its own,
    and the answer carries which of the four states it ended in.
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

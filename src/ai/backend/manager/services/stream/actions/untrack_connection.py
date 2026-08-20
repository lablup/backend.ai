from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class UntrackConnectionAction(BaseSingleEntityAction):
    kernel_id: KernelId
    session_id: SessionId
    service: str
    stream_id: str

    @override
    def entity_id(self) -> SessionID:
        return SessionID(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "untrack_stream_connection"


@dataclass(frozen=True)
class UntrackConnectionActionResult:
    kernel_id: KernelId
    remaining_count: int

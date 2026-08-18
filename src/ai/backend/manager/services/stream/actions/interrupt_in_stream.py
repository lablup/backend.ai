from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class InterruptInStreamAction(BaseSingleEntityAction):
    session_id: SessionId

    @override
    def entity_id(self) -> SessionID:
        return SessionID(self.session_id)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "interrupt_in_stream"


@dataclass(frozen=True)
class InterruptInStreamActionResult:
    result: dict[str, Any]

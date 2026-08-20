from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class GetStreamingSessionAction(BaseSingleEntityAction):
    session_id: SessionId

    @override
    def entity_id(self) -> SessionID:
        return SessionID(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_streaming_session"


@dataclass(frozen=True)
class GetStreamingSessionActionResult:
    session_id: SessionId
    kernel_id: KernelId
    kernel_host: str | None
    agent_addr: str | None
    repl_in_port: int
    repl_out_port: int
    service_ports: list[dict[str, Any]]

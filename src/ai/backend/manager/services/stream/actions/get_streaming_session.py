from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.stream.actions.base import StreamAction


@dataclass(frozen=True)
class GetStreamingSessionAction(StreamAction):
    session_name: str
    access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return self.session_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetStreamingSessionActionResult(BaseActionResult):
    session_id: str
    kernel_id: str
    kernel_host: str | None
    agent_addr: str | None
    repl_in_port: int
    repl_out_port: int
    service_ports: list[dict[str, Any]]

    @override
    def entity_id(self) -> str | None:
        return self.session_id

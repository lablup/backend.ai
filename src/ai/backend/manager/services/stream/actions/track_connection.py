from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.stream.actions.base import StreamAction


@dataclass(frozen=True)
class TrackConnectionAction(StreamAction):
    kernel_id: KernelId
    session_id: SessionId
    service: str
    stream_id: str

    @override
    def entity_id(self) -> str | None:
        return str(self.kernel_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class TrackConnectionActionResult(BaseActionResult):
    kernel_id: str

    @override
    def entity_id(self) -> str | None:
        return self.kernel_id

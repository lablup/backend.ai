from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import KernelId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.stream.actions.base import StreamAction


@dataclass(frozen=True)
class GCStaleConnectionsAction(StreamAction):
    active_session_ids: list[KernelId]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class GCStaleConnectionsActionResult(BaseActionResult):
    removed_sessions: list[str]

    @override
    def entity_id(self) -> str | None:
        return None

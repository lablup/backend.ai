from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.stream.actions.base import StreamAction


@dataclass(frozen=True)
class ExecuteInStreamAction(StreamAction):
    session_name: str
    access_key: AccessKey
    api_version: tuple[int, str]
    run_id: str
    mode: str
    code: str
    opts: dict[str, Any] = field(default_factory=dict)
    flush_timeout: float | None = None

    @override
    def entity_id(self) -> str | None:
        return self.session_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class ExecuteInStreamActionResult(BaseActionResult):
    result: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None

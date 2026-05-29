from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.stream.actions.base import StreamAction


@dataclass(frozen=True)
class StartServiceInStreamAction(StreamAction):
    session_name: str
    user_uuid: uuid.UUID
    service: str
    opts: dict[str, Any] = field(default_factory=dict)

    @override
    def entity_id(self) -> str | None:
        return self.session_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class StartServiceInStreamActionResult(BaseActionResult):
    result: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None

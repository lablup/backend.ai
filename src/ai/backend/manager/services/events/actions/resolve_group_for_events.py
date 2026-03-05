from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.events.actions.base import EventsAction


@dataclass(frozen=True)
class ResolveGroupForEventsAction(EventsAction):
    group_name: str

    @override
    def entity_id(self) -> str | None:
        return self.group_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ResolveGroupForEventsActionResult(BaseActionResult):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.group_id)

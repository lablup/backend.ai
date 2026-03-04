from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.events.actions.base import EventsAction


@dataclass(frozen=True)
class ResolveSessionForEventsAction(EventsAction):
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
class ResolveSessionForEventsActionResult(BaseActionResult):
    session_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)

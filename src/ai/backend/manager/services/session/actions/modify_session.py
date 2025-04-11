import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class SessionModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    priority: OptionalState[int] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.priority.update_dict(to_update, "priority")
        return to_update


@dataclass
class ModifySessionAction(SessionAction):
    session_id: uuid.UUID
    modifier: SessionModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)

    @override
    def operation_type(self):
        return "modify"


@dataclass
class ModifySessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_row: SessionRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)

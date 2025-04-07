import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ModifySessionInputData:
    name: Optional[str]
    priority: Optional[int]

    def set_attr(self, row: SessionRow):
        if self.name is not None:
            row.name = self.name
        if self.priority is not None:
            row.priority = self.priority


@dataclass
class ModifySessionAction(SessionAction):
    session_id: uuid.UUID
    props: ModifySessionInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

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

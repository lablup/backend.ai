import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction
from ai.backend.manager.types import TriState


@dataclass
class ModifyComputeSessionInputData:
    name: TriState[str] = field(default_factory=lambda: TriState.nop("name"))
    priority: TriState[int] = field(default_factory=lambda: TriState.nop("priority"))

    def set_attr(self, row: SessionRow) -> None:
        self.name.set_attr(row.name)
        self.priority.set_attr(row.priority)


# TODO: Rename ModifySessionAction?
@dataclass
class ModifyComputeSessionAction(SessionAction):
    session_id: uuid.UUID
    props: ModifyComputeSessionInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify"


@dataclass
class ModifyComputeSessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_row: SessionRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)

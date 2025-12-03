import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class DeleteGroupAction(GroupAction):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteGroupActionResult(BaseActionResult):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.group_id)

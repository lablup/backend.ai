import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.base import GroupAction


@dataclass
class DeleteGroupAction(GroupAction):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class DeleteGroupActionResult(BaseActionResult):
    data: Optional[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None

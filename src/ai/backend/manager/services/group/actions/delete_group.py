import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class DeleteGroupAction(GroupAction):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteGroupActionResult(BaseActionResult):
    group_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.group_id)

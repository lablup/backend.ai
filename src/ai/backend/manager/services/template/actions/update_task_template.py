from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction
from .create_task_template import TaskTemplateItemInput


@dataclass
class UpdateTaskTemplateAction(TemplateAction):
    """Action to update an existing task template."""

    template_id: str
    user_uuid: uuid.UUID
    group_id: uuid.UUID
    items: list[TaskTemplateItemInput] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.template_id


@dataclass
class UpdateTaskTemplateActionResult(BaseActionResult):
    """Result of updating a task template."""

    @override
    def entity_id(self) -> str | None:
        return None

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class GetTaskTemplateAction(TemplateAction):
    """Action to get a single task template by ID."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_task_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetTaskTemplateActionResult:
    """Result of getting a task template."""

    template: dict[str, Any]
    name: str
    user_uuid: uuid.UUID
    group_id: uuid.UUID

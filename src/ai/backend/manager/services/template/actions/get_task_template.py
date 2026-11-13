from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session_template.types import SessionTemplateData

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

    template: SessionTemplateData

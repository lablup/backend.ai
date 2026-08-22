from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class DeleteTaskTemplateAction(TemplateAction):
    """Action to soft-delete a task template."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_task_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteTaskTemplateActionResult:
    """Result of deleting a task template."""

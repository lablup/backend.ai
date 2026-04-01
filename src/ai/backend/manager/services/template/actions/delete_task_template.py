from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class DeleteTaskTemplateAction(TemplateAction):
    """Action to soft-delete a task template."""

    template_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return self.template_id


@dataclass
class DeleteTaskTemplateActionResult(BaseActionResult):
    """Result of deleting a task template."""

    @override
    def entity_id(self) -> str | None:
        return None

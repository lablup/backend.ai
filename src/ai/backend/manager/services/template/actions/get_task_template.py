from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class GetTaskTemplateAction(TemplateAction):
    """Action to get a single task template by ID."""

    template_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.template_id


@dataclass
class GetTaskTemplateActionResult(BaseActionResult):
    """Result of getting a task template."""

    template: dict[str, Any]
    name: str
    user_uuid: uuid.UUID
    group_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

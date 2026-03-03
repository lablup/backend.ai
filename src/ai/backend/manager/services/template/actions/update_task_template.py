from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction
from .create_task_template import TaskTemplateItemInput


@dataclass
class UpdateTaskTemplateAction(TemplateAction):
    """Action to update an existing task template."""

    template_id: str
    domain_name: str
    requesting_group: str
    requester_uuid: uuid.UUID
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None
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

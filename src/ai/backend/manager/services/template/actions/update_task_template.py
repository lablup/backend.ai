from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction
from .create_task_template import TaskTemplateItemInput


@dataclass
class UpdateTaskTemplateAction(TemplateAction):
    """Action to update an existing task template."""

    domain_name: str
    requesting_project: ProjectID
    requester_uuid: uuid.UUID
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None
    items: list[TaskTemplateItemInput] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_task_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateTaskTemplateActionResult:
    """Result of updating a task template."""

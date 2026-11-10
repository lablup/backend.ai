from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user.row import UserRole

from .base import TemplateScopeActionResult, TemplateUserScopeAction


@dataclass
class ListTaskTemplatesAction(TemplateUserScopeAction):
    """Action to list the task templates the requester may see."""

    user_role: UserRole
    domain_name: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_task_templates"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListTaskTemplatesActionResult(TemplateScopeActionResult):
    """Result of listing task templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)

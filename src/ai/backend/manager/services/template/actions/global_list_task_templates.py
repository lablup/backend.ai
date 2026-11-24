from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateGlobalAction


@dataclass(frozen=True)
class GlobalListTaskTemplatesAction(TemplateGlobalAction):
    """List the task templates of every user and project."""

    requester_id: UserID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_task_templates"


@dataclass(frozen=True)
class GlobalListTaskTemplatesActionResult:
    entries: list[dict[str, Any]] = field(default_factory=list)

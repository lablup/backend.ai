from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateScopeActionResult, TemplateUserScopeAction


@dataclass
class ListClusterTemplatesAction(TemplateUserScopeAction):
    """Action to list cluster templates with visibility control."""

    user_role: UserRole
    domain_name: str
    is_superadmin: bool
    list_all: bool
    group_id_filter: uuid.UUID | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_cluster_templates"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListClusterTemplatesActionResult(TemplateScopeActionResult):
    """Result of listing cluster templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)

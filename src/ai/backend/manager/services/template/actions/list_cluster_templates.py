from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction


@dataclass
class ListClusterTemplatesAction(TemplateAction):
    """Action to list cluster templates with visibility control."""

    user_uuid: uuid.UUID
    user_role: UserRole
    domain_name: str
    is_superadmin: bool
    list_all: bool
    group_id_filter: uuid.UUID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListClusterTemplatesActionResult(BaseActionResult):
    """Result of listing cluster templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction


@dataclass
class TaskTemplateItemInput:
    """Input for a single task template item in a batch create/update."""

    template: Mapping[str, Any]
    name: str | None = None
    group_id: uuid.UUID | None = None
    user_uuid: uuid.UUID | None = None


@dataclass
class CreatedTaskTemplateItem:
    """A single created template ID and owner user."""

    id: str
    user: str


@dataclass
class CreateTaskTemplateAction(TemplateAction):
    """Action to create one or more task templates."""

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
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class CreateTaskTemplateActionResult(BaseActionResult):
    """Result of creating task templates."""

    created: list[CreatedTaskTemplateItem] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

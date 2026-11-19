from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user.row import UserRole

from .base import TemplateProjectScopeAction, TemplateScopeActionResult


@dataclass
class TaskTemplateItemInput:
    """Input for a single task template item in a batch create/update."""

    template: Mapping[str, Any]
    name: str | None = None
    group_id: ProjectID | None = None
    user_uuid: UserID | None = None


@dataclass
class CreatedTaskTemplateItem:
    """A single created template ID and owner user."""

    id: SessionTemplateID
    user: UserID


@dataclass
class CreateTaskTemplateAction(TemplateProjectScopeAction):
    """Action to create one or more task templates."""

    domain_name: str
    requester_uuid: UserID
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None
    items: list[TaskTemplateItemInput] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_task_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateTaskTemplateActionResult(TemplateScopeActionResult):
    """Result of creating task templates."""

    created: list[CreatedTaskTemplateItem] = field(default_factory=list)

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(item.id for item in self.created)

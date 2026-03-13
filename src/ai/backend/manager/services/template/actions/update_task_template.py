from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.user import UserRole

from .base import TemplateSingleEntityAction, TemplateSingleEntityActionResult
from .create_task_template import TaskTemplateItemInput


@dataclass
class UpdateTaskTemplateAction(TemplateSingleEntityAction):
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
    def target_entity_id(self) -> str:
        return self.template_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION_TEMPLATE, self.template_id)


@dataclass
class UpdateTaskTemplateActionResult(TemplateSingleEntityActionResult):
    """Result of updating a task template."""

    _template_id: str = ""

    @override
    def target_entity_id(self) -> str:
        return self._template_id

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.user import UserRole

from .base import TemplateScopeAction, TemplateScopeActionResult


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
class CreateTaskTemplateAction(TemplateScopeAction):
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
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain_name)


@dataclass
class CreateTaskTemplateActionResult(TemplateScopeActionResult):
    """Result of creating task templates."""

    created: list[CreatedTaskTemplateItem] = field(default_factory=list)
    _domain_name: str = ""

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

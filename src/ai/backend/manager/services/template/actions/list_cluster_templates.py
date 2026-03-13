from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.user import UserRole

from .base import TemplateScopeAction, TemplateScopeActionResult


@dataclass
class ListClusterTemplatesAction(TemplateScopeAction):
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
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain_name)


@dataclass
class ListClusterTemplatesActionResult(TemplateScopeActionResult):
    """Result of listing cluster templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)
    _domain_name: str = ""

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

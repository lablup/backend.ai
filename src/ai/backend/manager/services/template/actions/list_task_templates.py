from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import TemplateScopeAction, TemplateScopeActionResult


@dataclass
class ListTaskTemplatesAction(TemplateScopeAction):
    """Action to list all active task templates."""

    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_uuid))


@dataclass
class ListTaskTemplatesActionResult(TemplateScopeActionResult):
    """Result of listing task templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)
    _user_uuid: str = ""

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self._user_uuid

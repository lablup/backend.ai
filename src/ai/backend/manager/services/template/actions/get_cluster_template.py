from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import TemplateSingleEntityAction, TemplateSingleEntityActionResult


@dataclass
class GetClusterTemplateAction(TemplateSingleEntityAction):
    """Action to get a single cluster template by ID."""

    template_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return self.template_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION_TEMPLATE, self.template_id)


@dataclass
class GetClusterTemplateActionResult(TemplateSingleEntityActionResult):
    """Result of getting a cluster template."""

    template: dict[str, Any]
    _template_id: str = ""

    @override
    def target_entity_id(self) -> str:
        return self._template_id

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import TemplateSingleEntityAction, TemplateSingleEntityActionResult


@dataclass
class DeleteClusterTemplateAction(TemplateSingleEntityAction):
    """Action to soft-delete a cluster template."""

    template_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return self.template_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION_TEMPLATE, self.template_id)


@dataclass
class DeleteClusterTemplateActionResult(TemplateSingleEntityActionResult):
    """Result of deleting a cluster template."""

    _template_id: str = ""

    @override
    def target_entity_id(self) -> str:
        return self._template_id

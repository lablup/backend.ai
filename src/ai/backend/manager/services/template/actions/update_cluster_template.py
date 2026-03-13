from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import TemplateSingleEntityAction, TemplateSingleEntityActionResult


@dataclass
class UpdateClusterTemplateAction(TemplateSingleEntityAction):
    """Action to update an existing cluster template."""

    template_id: str
    template_data: Mapping[str, Any]

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
class UpdateClusterTemplateActionResult(TemplateSingleEntityActionResult):
    """Result of updating a cluster template."""

    _template_id: str = ""

    @override
    def target_entity_id(self) -> str:
        return self._template_id

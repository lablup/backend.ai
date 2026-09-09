from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import (
    EntityType,
    GlobalEntityType,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class GetResourceSlotsAction(BaseGlobalAction):
    """Action to get system-wide known resource slots."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_slots"


@dataclass
class GetResourceSlotsActionResult:
    """Result of getting resource slots."""

    slots: dict[str, Any]

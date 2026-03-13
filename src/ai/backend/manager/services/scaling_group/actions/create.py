from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.creator import Creator

from .base import ScalingGroupScopeAction, ScalingGroupScopeActionResult


@dataclass
class CreateScalingGroupAction(ScalingGroupScopeAction):
    """Action to create a scaling group."""

    creator: Creator[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, "*")


@dataclass
class CreateScalingGroupActionResult(ScalingGroupScopeActionResult):
    """Result of creating a scaling group."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group.name

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"

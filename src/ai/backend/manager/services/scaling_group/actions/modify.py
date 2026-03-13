from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import ScalingGroupSingleEntityAction, ScalingGroupSingleEntityActionResult


@dataclass
class ModifyScalingGroupAction(ScalingGroupSingleEntityAction):
    """Action to modify a scaling group."""

    updater: Updater[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.RESOURCE_GROUP, str(self.updater.pk_value))

    @override
    def field_data(self) -> FieldData | None:
        return None


@dataclass
class ModifyScalingGroupActionResult(ScalingGroupSingleEntityActionResult):
    """Result of modifying a scaling group."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group.name

    @override
    def target_entity_id(self) -> str:
        return self.scaling_group.name

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.purger import Purger

from .base import ScalingGroupSingleEntityAction, ScalingGroupSingleEntityActionResult


@dataclass
class PurgeScalingGroupAction(ScalingGroupSingleEntityAction):
    """Action to purge a scaling group by name, including all related sessions and routes."""

    purger: Purger[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.RESOURCE_GROUP, str(self.purger.pk_value))

    @override
    def field_data(self) -> FieldData | None:
        return None


@dataclass
class PurgeScalingGroupActionResult(ScalingGroupSingleEntityActionResult):
    """Result of purging a scaling group."""

    data: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.data.name

    @override
    def target_entity_id(self) -> str:
        return self.data.name

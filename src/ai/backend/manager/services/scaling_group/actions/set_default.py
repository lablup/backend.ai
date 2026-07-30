from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.scaling_group.types import ScalingGroupData

from .base import ScalingGroupAction


@dataclass(frozen=True)
class SetDefaultScalingGroupAction(ScalingGroupAction):
    """Action to designate a scaling group as the default one, or to clear its default flag.

    At most one scaling group is the default at a time, so setting the flag on one group
    clears it on the incumbent. Clearing leaves the system without any default.
    """

    resource_group: ResourceGroupName
    is_default: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str:
        return str(self.resource_group)


@dataclass(frozen=True)
class SetDefaultScalingGroupActionResult(BaseActionResult):
    """Result of designating (or clearing) the default scaling group."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group.name

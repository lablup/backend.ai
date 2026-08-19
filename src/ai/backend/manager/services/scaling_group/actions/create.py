from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.creator import Creator

from .base import ScalingGroupGlobalAction


@dataclass(frozen=True)
class CreateScalingGroupAction(ScalingGroupGlobalAction):
    """Action to create a scaling group."""

    creator: Creator[ScalingGroupRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class CreateScalingGroupActionResult:
    """Result of creating a scaling group."""

    scaling_group: ScalingGroupData

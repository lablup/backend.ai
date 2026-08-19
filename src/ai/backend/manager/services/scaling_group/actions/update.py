from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import ScalingGroupAction


@dataclass(frozen=True)
class UpdateScalingGroupAction(ScalingGroupAction):
    """Action to modify a scaling group."""

    updater: Updater[ScalingGroupRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateScalingGroupActionResult:
    """Result of modifying a scaling group."""

    scaling_group: ScalingGroupData

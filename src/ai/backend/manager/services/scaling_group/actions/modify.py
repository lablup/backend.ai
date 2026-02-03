from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import ScalingGroupAction


@dataclass
class ModifyScalingGroupAction(ScalingGroupAction):
    """Action to modify a scaling group."""

    updater: Updater[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)


@dataclass
class ModifyScalingGroupActionResult(BaseActionResult):
    """Result of modifying a scaling group."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group.name

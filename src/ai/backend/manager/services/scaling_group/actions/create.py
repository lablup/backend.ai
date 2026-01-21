from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.creator import Creator

from .base import ScalingGroupAction


@dataclass
class CreateScalingGroupAction(ScalingGroupAction):
    """Action to create a scaling group."""

    creator: Creator[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class CreateScalingGroupActionResult(BaseActionResult):
    """Result of creating a scaling group."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> Optional[str]:
        return self.scaling_group.name

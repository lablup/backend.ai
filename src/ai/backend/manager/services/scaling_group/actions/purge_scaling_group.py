from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass
class PurgeScalingGroupAction(ScalingGroupAction):
    """Action to purge a scaling group by name, including all related sessions and routes."""

    purger: Purger[ScalingGroupRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purger.pk_value)


@dataclass
class PurgeScalingGroupActionResult(BaseActionResult):
    """Result of purging a scaling group."""

    data: ScalingGroupData

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name

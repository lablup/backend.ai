from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import Purger
from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass
class PurgeScalingGroupAction(ScalingGroupAction):
    purger: Purger[ScalingGroupRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge"


@dataclass
class PurgeScalingGroupActionResult(BaseActionResult):
    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> Optional[str]:
        return self.scaling_group.name

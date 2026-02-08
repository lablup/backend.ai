from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass
class ScalingGroupDomainAction(ScalingGroupAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP_DOMAIN

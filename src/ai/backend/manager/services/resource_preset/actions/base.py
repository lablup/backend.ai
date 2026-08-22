from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class ResourcePresetAction(BaseGlobalAction):
    """Base for the resource preset operations.

    A preset is installation-wide configuration reached by id or by name, so no
    operation here names an entity.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_PRESET_ENTITY_TYPE

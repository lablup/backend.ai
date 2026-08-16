from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("RolePresetID",)


class RolePresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("RolePermissionPresetID",)


class RolePermissionPresetID(FieldIdentifier):
    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

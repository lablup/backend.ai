from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = (
    "ROLE_PERMISSION_PRESET_FIELD_TYPE",
    "RolePermissionPresetFieldType",
    "RolePermissionPresetID",
)


class RolePermissionPresetFieldType(FieldType):
    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE


ROLE_PERMISSION_PRESET_FIELD_TYPE = RolePermissionPresetFieldType("role:permission")


class RolePermissionPresetID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ROLE_PERMISSION_PRESET_FIELD_TYPE

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("RolePermissionPresetID",)


ROLE_PERMISSION_PRESET_FIELD_TYPE = FieldType("role_permission_preset")


class RolePermissionPresetID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ROLE_PERMISSION_PRESET_FIELD_TYPE

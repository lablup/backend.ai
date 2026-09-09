from typing import override

from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("RolePermissionPresetID",)


class RolePermissionPresetFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "role_permission_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "One permission a role preset grants."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return RolePresetEntityType


class RolePermissionPresetID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return RolePermissionPresetFieldType()

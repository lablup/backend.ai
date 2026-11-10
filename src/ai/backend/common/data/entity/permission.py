from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "PermissionFieldType",
    "PermissionID",
)


class PermissionFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "permission"

    @override
    @classmethod
    def description(cls) -> str:
        return "One permission a role grants on one entity type, within one scope."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return RoleEntityType


class PermissionID(FieldIdentifier):
    """The id of one ``permissions`` row — a field row of the role holding it."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return PermissionFieldType()

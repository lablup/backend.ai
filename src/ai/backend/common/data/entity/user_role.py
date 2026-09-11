from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "UserRoleFieldType",
    "UserRoleAssignmentID",
)


class UserRoleFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user_role"

    @override
    @classmethod
    def description(cls) -> str:
        return "One role a user holds."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class UserRoleAssignmentID(FieldIdentifier):
    """The id of one ``user_roles`` row — a field row of the user holding the role."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return UserRoleFieldType()

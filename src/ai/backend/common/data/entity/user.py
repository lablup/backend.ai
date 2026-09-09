from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "UserEntityType",
    "USER_SCOPE_TYPE",
    "UserID",
)


class UserEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user"

    @override
    @classmethod
    def description(cls) -> str:
        return "An account inside a domain."


USER_SCOPE_TYPE = ScopeType(UserEntityType())


class UserID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return UserEntityType()

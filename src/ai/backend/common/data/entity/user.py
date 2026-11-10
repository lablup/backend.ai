from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "UserEntityType",
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


class UserID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return UserEntityType()

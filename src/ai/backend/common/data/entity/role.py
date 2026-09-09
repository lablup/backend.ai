from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RoleEntityType",
    "RoleID",
)


class RoleEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "role"

    @override
    @classmethod
    def description(cls) -> str:
        return "A named set of permissions granted in a scope."


class RoleID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RoleEntityType()

import enum
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, GlobalEntityType

__all__ = (
    "GlobalEntityID",
    "GlobalEntityName",
)


class GlobalEntityName(enum.StrEnum):
    """The singleton scopes of the `global` entity type, one row each in `global_entities`."""

    GLOBAL = "global"
    PUBLIC = "public"


class GlobalEntityID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return GlobalEntityType()

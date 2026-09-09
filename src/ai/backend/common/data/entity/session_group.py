from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "SessionGroupEntityType",
    "SessionGroupID",
)


class SessionGroupEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session_group"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "A set of sessions packed onto the same agents or spread across them, strictly"
            " or as a preference."
        )


class SessionGroupID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return SessionGroupEntityType()

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "SESSION_GROUP_ENTITY_TYPE",
    "SessionGroupID",
)


SESSION_GROUP_ENTITY_TYPE = EntityType("session_group")


class SessionGroupID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return SESSION_GROUP_ENTITY_TYPE

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "SESSION_ENTITY_TYPE",
    "SESSION_SCOPE_TYPE",
    "SessionID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.SESSION value.
SESSION_ENTITY_TYPE = EntityType("session")
SESSION_SCOPE_TYPE = ScopeType(SESSION_ENTITY_TYPE)


class SessionID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "USER_ENTITY_TYPE",
    "USER_SCOPE_TYPE",
    "UserID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.USER value.
USER_ENTITY_TYPE = EntityType("user")
USER_SCOPE_TYPE = ScopeType(USER_ENTITY_TYPE)


class UserID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

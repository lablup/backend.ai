from typing import NewType
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "USER_ENTITY_TYPE",
    "USER_SCOPE_TYPE",
    "UserID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.USER value.
USER_ENTITY_TYPE = EntityType("user")
USER_SCOPE_TYPE = ScopeType(USER_ENTITY_TYPE)

UserID = NewType("UserID", UUID)

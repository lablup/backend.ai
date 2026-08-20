from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ROLE_ENTITY_TYPE",
    "RoleID",
)


# Raw string mirroring the RBAC-managed role element value.
ROLE_ENTITY_TYPE = EntityType("role")


class RoleID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ROLE_ENTITY_TYPE

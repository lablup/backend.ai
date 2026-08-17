from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "PROJECT_ENTITY_TYPE",
    "PROJECT_SCOPE_TYPE",
    "ProjectID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.PROJECT value.
PROJECT_ENTITY_TYPE = EntityType("project")
PROJECT_SCOPE_TYPE = ScopeType(PROJECT_ENTITY_TYPE)


class ProjectID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

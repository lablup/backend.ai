from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "PROJECT_ENTITY_TYPE",
    "PROJECT_SCOPE_TYPE",
)


# Raw strings mirroring the RBAC-managed RBACElementType.PROJECT value.
PROJECT_ENTITY_TYPE = EntityType("project")
PROJECT_SCOPE_TYPE = ScopeType(PROJECT_ENTITY_TYPE)

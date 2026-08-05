from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "PROJECT_ENTITY_TYPE",
    "PROJECT_SCOPE_TYPE",
)


# Raw strings mirroring the RBAC-managed RBACElementType.PROJECT value.
PROJECT_SCOPE_TYPE = ScopeType("project")
PROJECT_ENTITY_TYPE = EntityType("project")

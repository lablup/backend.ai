from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "RESOURCE_GROUP_ENTITY_TYPE",
    "RESOURCE_GROUP_SCOPE_TYPE",
)


# Raw strings mirroring the RBAC-managed RBACElementType.RESOURCE_GROUP value.
RESOURCE_GROUP_ENTITY_TYPE = EntityType("resource_group")
RESOURCE_GROUP_SCOPE_TYPE = ScopeType(RESOURCE_GROUP_ENTITY_TYPE)

from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "DOMAIN_ENTITY_TYPE",
    "DOMAIN_SCOPE_TYPE",
)


# Raw strings mirroring the RBAC-managed RBACElementType.DOMAIN value.
DOMAIN_SCOPE_TYPE = ScopeType("domain")
DOMAIN_ENTITY_TYPE = EntityType("domain")

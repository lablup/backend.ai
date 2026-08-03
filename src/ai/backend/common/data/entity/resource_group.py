from ai.backend.common.data.entity.types import ScopeType

__all__ = ("RESOURCE_GROUP_SCOPE_TYPE",)


# Raw string mirroring the RBAC-managed RBACElementType.RESOURCE_GROUP value.
RESOURCE_GROUP_SCOPE_TYPE = ScopeType("resource_group")

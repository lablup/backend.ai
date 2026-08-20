from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "CONTAINER_REGISTRY_ENTITY_TYPE",
    "CONTAINER_REGISTRY_SCOPE_TYPE",
    "ContainerRegistryID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.CONTAINER_REGISTRY value.
CONTAINER_REGISTRY_ENTITY_TYPE = EntityType("container_registry")
CONTAINER_REGISTRY_SCOPE_TYPE = ScopeType(CONTAINER_REGISTRY_ENTITY_TYPE)


class ContainerRegistryID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return CONTAINER_REGISTRY_ENTITY_TYPE

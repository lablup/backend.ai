import uuid
from typing import NewType

from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "CONTAINER_REGISTRY_ENTITY_TYPE",
    "CONTAINER_REGISTRY_SCOPE_TYPE",
    "ContainerRegistryID",
)


# Raw strings mirroring the RBAC-managed RBACElementType.CONTAINER_REGISTRY value.
CONTAINER_REGISTRY_ENTITY_TYPE = EntityType("container_registry")
CONTAINER_REGISTRY_SCOPE_TYPE = ScopeType(CONTAINER_REGISTRY_ENTITY_TYPE)

ContainerRegistryID = NewType("ContainerRegistryID", uuid.UUID)

"""GraphQL container registry module."""

from .resolver import (
    admin_container_registries_v2,
    admin_create_container_registry_v2,
    admin_delete_container_registry_v2,
    admin_update_container_registry_v2,
)
from .types import (
    ContainerRegistryGQL,
    ContainerRegistryTypeGQL,
    ContainerRegistryV2Connection,
)

__all__ = (
    "ContainerRegistryGQL",
    "ContainerRegistryTypeGQL",
    "ContainerRegistryV2Connection",
    "admin_container_registries_v2",
    "admin_create_container_registry_v2",
    "admin_delete_container_registry_v2",
    "admin_update_container_registry_v2",
)

"""Field type and id of the association_container_registries_groups table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("CONTAINER_REGISTRY_GROUP_FIELD_TYPE", "ContainerRegistryGroupID")

CONTAINER_REGISTRY_GROUP_FIELD_TYPE = FieldType("container_registry_group")


class ContainerRegistryGroupID(FieldIdentifier):
    """A registry-project association row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return CONTAINER_REGISTRY_GROUP_FIELD_TYPE

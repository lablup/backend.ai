from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ComputeClusterEntityType",
    "ComputeClusterID",
)


class ComputeClusterEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "compute_cluster"

    @override
    @classmethod
    def description(cls) -> str:
        return "A Kubernetes cluster that runs the sessions of Kubernetes-backed resource groups."


class ComputeClusterID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ComputeClusterEntityType()

from dataclasses import dataclass

from ai.backend.common.data.entity.container_registry import ContainerRegistryID


@dataclass(frozen=True)
class DomainContainerRegistryRelationChange:
    """The registries a relation update linked to a domain and the ones it unlinked."""

    linked: list[ContainerRegistryID]
    unlinked: list[ContainerRegistryID]

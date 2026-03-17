"""Central registry of all domain adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


class Adapters:
    """Container holding all domain adapters.

    Instantiated once at application startup and injected into both
    GQL context (``StrawberryGQLContext.adapters``) and REST handler
    dependencies.  New domain adapters are added as fields here.
    """

    def __init__(
        self,
        container_registry: ContainerRegistryAdapter,
    ) -> None:
        self.container_registry = container_registry

    @classmethod
    def create(cls, processors: Processors) -> Adapters:
        """Factory that wires up all adapters from the shared Processors."""
        return cls(
            container_registry=ContainerRegistryAdapter(processors),
        )

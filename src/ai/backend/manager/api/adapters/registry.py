"""Central registry of all domain adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapters.agent import AgentAdapter
from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.scheduling_history import SchedulingHistoryAdapter
from ai.backend.manager.api.adapters.service_catalog import ServiceCatalogAdapter
from ai.backend.manager.api.adapters.session import SessionAdapter

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
        agent: AgentAdapter,
        container_registry: ContainerRegistryAdapter,
        scheduling_history: SchedulingHistoryAdapter,
        service_catalog: ServiceCatalogAdapter,
        session: SessionAdapter,
    ) -> None:
        self.agent = agent
        self.container_registry = container_registry
        self.scheduling_history = scheduling_history
        self.service_catalog = service_catalog
        self.session = session

    @classmethod
    def create(cls, processors: Processors) -> Adapters:
        """Factory that wires up all adapters from the shared Processors."""
        return cls(
            agent=AgentAdapter(processors),
            container_registry=ContainerRegistryAdapter(processors),
            scheduling_history=SchedulingHistoryAdapter(processors),
            service_catalog=ServiceCatalogAdapter(processors),
            session=SessionAdapter(processors),
        )

"""Central registry of all domain adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapters.agent import AgentAdapter
from ai.backend.manager.api.adapters.artifact import ArtifactAdapter
from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.domain import DomainAdapter
from ai.backend.manager.api.adapters.image import ImageAdapter
from ai.backend.manager.api.adapters.notification import NotificationAdapter
from ai.backend.manager.api.adapters.object_storage import ObjectStorageAdapter
from ai.backend.manager.api.adapters.project import ProjectAdapter
from ai.backend.manager.api.adapters.prometheus_query_preset import PrometheusQueryPresetAdapter
from ai.backend.manager.api.adapters.rbac import RBACAdapter
from ai.backend.manager.api.adapters.resource_group import ResourceGroupAdapter
from ai.backend.manager.api.adapters.resource_slot import ResourceSlotAdapter
from ai.backend.manager.api.adapters.scheduling_history import SchedulingHistoryAdapter
from ai.backend.manager.api.adapters.service_catalog import ServiceCatalogAdapter
from ai.backend.manager.api.adapters.session import SessionAdapter
from ai.backend.manager.api.adapters.user import UserAdapter

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
        artifact: ArtifactAdapter,
        container_registry: ContainerRegistryAdapter,
        domain: DomainAdapter,
        image: ImageAdapter,
        notification: NotificationAdapter,
        object_storage: ObjectStorageAdapter,
        project: ProjectAdapter,
        prometheus_query_preset: PrometheusQueryPresetAdapter,
        rbac: RBACAdapter,
        resource_group: ResourceGroupAdapter,
        resource_slot: ResourceSlotAdapter,
        scheduling_history: SchedulingHistoryAdapter,
        service_catalog: ServiceCatalogAdapter,
        session: SessionAdapter,
        user: UserAdapter,
    ) -> None:
        self.agent = agent
        self.artifact = artifact
        self.container_registry = container_registry
        self.domain = domain
        self.image = image
        self.notification = notification
        self.object_storage = object_storage
        self.project = project
        self.prometheus_query_preset = prometheus_query_preset
        self.rbac = rbac
        self.resource_group = resource_group
        self.resource_slot = resource_slot
        self.scheduling_history = scheduling_history
        self.service_catalog = service_catalog
        self.session = session
        self.user = user

    @classmethod
    def create(cls, processors: Processors) -> Adapters:
        """Factory that wires up all adapters from the shared Processors."""
        return cls(
            agent=AgentAdapter(processors),
            artifact=ArtifactAdapter(processors),
            container_registry=ContainerRegistryAdapter(processors),
            domain=DomainAdapter(processors),
            image=ImageAdapter(processors),
            notification=NotificationAdapter(processors),
            object_storage=ObjectStorageAdapter(processors),
            project=ProjectAdapter(processors),
            prometheus_query_preset=PrometheusQueryPresetAdapter(processors),
            rbac=RBACAdapter(processors),
            resource_group=ResourceGroupAdapter(processors),
            resource_slot=ResourceSlotAdapter(processors),
            scheduling_history=SchedulingHistoryAdapter(processors),
            service_catalog=ServiceCatalogAdapter(processors),
            session=SessionAdapter(processors),
            user=UserAdapter(processors),
        )

"""Central registry of all domain adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapters.agent import AgentAdapter
from ai.backend.manager.api.adapters.app_config import AppConfigAdapter
from ai.backend.manager.api.adapters.artifact import ArtifactAdapter
from ai.backend.manager.api.adapters.artifact_registry import ArtifactRegistryAdapter
from ai.backend.manager.api.adapters.audit_log import AuditLogAdapter
from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.deployment import DeploymentAdapter
from ai.backend.manager.api.adapters.domain import DomainAdapter
from ai.backend.manager.api.adapters.fair_share import FairShareAdapter
from ai.backend.manager.api.adapters.huggingface_registry import HuggingFaceRegistryAdapter
from ai.backend.manager.api.adapters.image import ImageAdapter
from ai.backend.manager.api.adapters.login_history import LoginHistoryAdapter
from ai.backend.manager.api.adapters.login_session import LoginSessionAdapter
from ai.backend.manager.api.adapters.notification import NotificationAdapter
from ai.backend.manager.api.adapters.object_storage import ObjectStorageAdapter
from ai.backend.manager.api.adapters.project import ProjectAdapter
from ai.backend.manager.api.adapters.prometheus_query_preset import PrometheusQueryPresetAdapter
from ai.backend.manager.api.adapters.rbac import RBACAdapter
from ai.backend.manager.api.adapters.reservoir_registry import ReservoirRegistryAdapter
from ai.backend.manager.api.adapters.resource_allocation import ResourceAllocationAdapter
from ai.backend.manager.api.adapters.resource_group import ResourceGroupAdapter
from ai.backend.manager.api.adapters.resource_policy import ResourcePolicyAdapter
from ai.backend.manager.api.adapters.resource_preset import ResourcePresetAdapter
from ai.backend.manager.api.adapters.resource_slot import ResourceSlotAdapter
from ai.backend.manager.api.adapters.resource_usage import ResourceUsageAdapter
from ai.backend.manager.api.adapters.runtime_variant import RuntimeVariantAdapter
from ai.backend.manager.api.adapters.scheduling_history import SchedulingHistoryAdapter
from ai.backend.manager.api.adapters.service_catalog import ServiceCatalogAdapter
from ai.backend.manager.api.adapters.session import SessionAdapter
from ai.backend.manager.api.adapters.storage_namespace import StorageNamespaceAdapter
from ai.backend.manager.api.adapters.user import UserAdapter
from ai.backend.manager.api.adapters.vfolder import VFolderAdapter
from ai.backend.manager.api.adapters.vfs_storage import VFSStorageAdapter

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.config.unified import AuthConfig
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
        app_config: AppConfigAdapter,
        artifact: ArtifactAdapter,
        artifact_registry: ArtifactRegistryAdapter,
        audit_log: AuditLogAdapter,
        container_registry: ContainerRegistryAdapter,
        deployment: DeploymentAdapter,
        domain: DomainAdapter,
        fair_share: FairShareAdapter,
        huggingface_registry: HuggingFaceRegistryAdapter,
        image: ImageAdapter,
        login_history: LoginHistoryAdapter,
        login_session: LoginSessionAdapter,
        notification: NotificationAdapter,
        object_storage: ObjectStorageAdapter,
        project: ProjectAdapter,
        prometheus_query_preset: PrometheusQueryPresetAdapter,
        rbac: RBACAdapter,
        reservoir_registry: ReservoirRegistryAdapter,
        resource_allocation: ResourceAllocationAdapter,
        resource_group: ResourceGroupAdapter,
        resource_policy: ResourcePolicyAdapter,
        resource_preset: ResourcePresetAdapter,
        resource_slot: ResourceSlotAdapter,
        runtime_variant: RuntimeVariantAdapter,
        resource_usage: ResourceUsageAdapter,
        scheduling_history: SchedulingHistoryAdapter,
        service_catalog: ServiceCatalogAdapter,
        session: SessionAdapter,
        storage_namespace: StorageNamespaceAdapter,
        user: UserAdapter,
        vfolder: VFolderAdapter,
        vfs_storage: VFSStorageAdapter,
    ) -> None:
        self.agent = agent
        self.app_config = app_config
        self.artifact = artifact
        self.artifact_registry = artifact_registry
        self.audit_log = audit_log
        self.container_registry = container_registry
        self.deployment = deployment
        self.domain = domain
        self.fair_share = fair_share
        self.huggingface_registry = huggingface_registry
        self.image = image
        self.login_history = login_history
        self.login_session = login_session
        self.notification = notification
        self.object_storage = object_storage
        self.project = project
        self.prometheus_query_preset = prometheus_query_preset
        self.rbac = rbac
        self.reservoir_registry = reservoir_registry
        self.resource_allocation = resource_allocation
        self.resource_group = resource_group
        self.resource_policy = resource_policy
        self.resource_preset = resource_preset
        self.resource_slot = resource_slot
        self.runtime_variant = runtime_variant
        self.resource_usage = resource_usage
        self.scheduling_history = scheduling_history
        self.service_catalog = service_catalog
        self.session = session
        self.storage_namespace = storage_namespace
        self.user = user
        self.vfolder = vfolder
        self.vfs_storage = vfs_storage

    @classmethod
    def create(
        cls,
        processors: Processors,
        auth_config: AuthConfig,
        config_provider: ManagerConfigProvider | None = None,
    ) -> Adapters:
        """Factory that wires up all adapters from the shared Processors."""
        return cls(
            agent=AgentAdapter(processors),
            app_config=AppConfigAdapter(processors),
            artifact=ArtifactAdapter(processors),
            artifact_registry=ArtifactRegistryAdapter(processors),
            audit_log=AuditLogAdapter(processors),
            container_registry=ContainerRegistryAdapter(processors),
            deployment=DeploymentAdapter(processors),
            domain=DomainAdapter(processors),
            fair_share=FairShareAdapter(processors),
            huggingface_registry=HuggingFaceRegistryAdapter(processors),
            image=ImageAdapter(processors),
            login_history=LoginHistoryAdapter(processors),
            login_session=LoginSessionAdapter(processors),
            notification=NotificationAdapter(processors),
            object_storage=ObjectStorageAdapter(processors),
            project=ProjectAdapter(processors),
            prometheus_query_preset=PrometheusQueryPresetAdapter(processors),
            rbac=RBACAdapter(processors),
            reservoir_registry=ReservoirRegistryAdapter(processors),
            resource_allocation=ResourceAllocationAdapter(processors, config_provider),
            resource_group=ResourceGroupAdapter(processors),
            resource_policy=ResourcePolicyAdapter(processors),
            resource_preset=ResourcePresetAdapter(processors),
            resource_slot=ResourceSlotAdapter(processors),
            runtime_variant=RuntimeVariantAdapter(processors),
            resource_usage=ResourceUsageAdapter(processors),
            scheduling_history=SchedulingHistoryAdapter(processors),
            service_catalog=ServiceCatalogAdapter(processors),
            session=SessionAdapter(processors),
            storage_namespace=StorageNamespaceAdapter(processors),
            user=UserAdapter(processors, auth_config),
            vfolder=VFolderAdapter(processors),
            vfs_storage=VFSStorageAdapter(processors),
        )

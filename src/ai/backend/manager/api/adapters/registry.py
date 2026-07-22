"""Central registry of all domain adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.api.adapters.app_config_fragment.adapter import (
    AppConfigFragmentAdapter,
)
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.api.adapters.artifact_registry.adapter import ArtifactRegistryAdapter
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.api.adapters.huggingface_registry.adapter import HuggingFaceRegistryAdapter
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.adapters.reservoir_registry.adapter import ReservoirRegistryAdapter
from ai.backend.manager.api.adapters.resource_allocation.adapter import ResourceAllocationAdapter
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.api.adapters.resource_usage.adapter import ResourceUsageAdapter
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.api.adapters.scheduling_handler.adapter import SchedulingHandlerAdapter
from ai.backend.manager.api.adapters.scheduling_history.adapter import SchedulingHistoryAdapter
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.api.adapters.storage_host.adapter import StorageHostAdapter
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.services.processors import Processors
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator


class Adapters:
    """Container holding all domain adapters.

    Instantiated once at application startup and injected into both
    GQL context (``StrawberryGQLContext.adapters``) and REST handler
    dependencies.  New domain adapters are added as fields here.
    """

    def __init__(
        self,
        agent: AgentAdapter,
        app_config_fragment: AppConfigFragmentAdapter,
        app_config_allow_list: AppConfigAllowListAdapter,
        app_config_definition: AppConfigDefinitionAdapter,
        artifact: ArtifactAdapter,
        artifact_registry: ArtifactRegistryAdapter,
        audit_log: AuditLogAdapter,
        container_registry: ContainerRegistryAdapter,
        deployment: DeploymentAdapter,
        domain: DomainAdapter,
        fair_share: FairShareAdapter,
        huggingface_registry: HuggingFaceRegistryAdapter,
        image: ImageAdapter,
        login_client_type: LoginClientTypeAdapter,
        login_history: LoginHistoryAdapter,
        login_session: LoginSessionAdapter,
        notification: NotificationAdapter,
        object_storage: ObjectStorageAdapter,
        project: ProjectAdapter,
        prometheus_query_preset: PrometheusQueryPresetAdapter,
        prometheus_query_preset_category: PrometheusQueryPresetCategoryAdapter,
        rbac: RBACAdapter,
        reservoir_registry: ReservoirRegistryAdapter,
        resource_allocation: ResourceAllocationAdapter,
        resource_group: ResourceGroupAdapter,
        resource_policy: ResourcePolicyAdapter,
        resource_preset: ResourcePresetAdapter,
        resource_slot: ResourceSlotAdapter,
        retention_policy: RetentionPolicyAdapter,
        runtime_variant: RuntimeVariantAdapter,
        runtime_variant_preset: RuntimeVariantPresetAdapter,
        deployment_revision_preset: DeploymentRevisionPresetAdapter,
        model_card: ModelCardAdapter,
        resource_usage: ResourceUsageAdapter,
        role_preset: RolePresetAdapter,
        scheduling_handler: SchedulingHandlerAdapter,
        scheduling_history: SchedulingHistoryAdapter,
        service_catalog: ServiceCatalogAdapter,
        session: SessionAdapter,
        storage_host: StorageHostAdapter,
        storage_namespace: StorageNamespaceAdapter,
        user: UserAdapter,
        vfolder: VFolderAdapter,
        vfs_storage: VFSStorageAdapter,
    ) -> None:
        self.agent = agent
        self.app_config_fragment = app_config_fragment
        self.app_config_allow_list = app_config_allow_list
        self.app_config_definition = app_config_definition
        self.artifact = artifact
        self.artifact_registry = artifact_registry
        self.audit_log = audit_log
        self.container_registry = container_registry
        self.deployment = deployment
        self.domain = domain
        self.fair_share = fair_share
        self.huggingface_registry = huggingface_registry
        self.image = image
        self.login_client_type = login_client_type
        self.login_history = login_history
        self.login_session = login_session
        self.notification = notification
        self.object_storage = object_storage
        self.project = project
        self.prometheus_query_preset = prometheus_query_preset
        self.prometheus_query_preset_category = prometheus_query_preset_category
        self.rbac = rbac
        self.reservoir_registry = reservoir_registry
        self.resource_allocation = resource_allocation
        self.resource_group = resource_group
        self.resource_policy = resource_policy
        self.resource_preset = resource_preset
        self.resource_slot = resource_slot
        self.retention_policy = retention_policy
        self.runtime_variant = runtime_variant
        self.runtime_variant_preset = runtime_variant_preset
        self.deployment_revision_preset = deployment_revision_preset
        self.model_card = model_card
        self.resource_usage = resource_usage
        self.role_preset = role_preset
        self.scheduling_handler = scheduling_handler
        self.scheduling_history = scheduling_history
        self.service_catalog = service_catalog
        self.session = session
        self.storage_host = storage_host
        self.storage_namespace = storage_namespace
        self.user = user
        self.vfolder = vfolder
        self.vfs_storage = vfs_storage

    @classmethod
    def create(
        cls,
        processors: Processors,
        auth_config: AuthConfig,
        deployment_coordinator: DeploymentCoordinator,
        schedule_coordinator: ScheduleCoordinator,
        config_provider: ManagerConfigProvider | None = None,
    ) -> Adapters:
        """Factory that wires up all adapters from the shared Processors.

        ``deployment_coordinator`` / ``schedule_coordinator`` are
        threaded through to adapters that validate or enumerate live
        handler names (``DeploymentAdapter``, ``ResourceGroupAdapter``,
        ``SchedulingHandlerAdapter``) so that DTO-side validation and
        catalog endpoints always agree with the coordinators' live
        registrations.
        """
        return cls(
            agent=AgentAdapter(processors),
            app_config_fragment=AppConfigFragmentAdapter(processors),
            app_config_allow_list=AppConfigAllowListAdapter(processors),
            app_config_definition=AppConfigDefinitionAdapter(processors),
            artifact=ArtifactAdapter(processors),
            artifact_registry=ArtifactRegistryAdapter(processors),
            audit_log=AuditLogAdapter(processors),
            container_registry=ContainerRegistryAdapter(processors),
            deployment=DeploymentAdapter(processors, deployment_coordinator),
            domain=DomainAdapter(processors),
            fair_share=FairShareAdapter(processors),
            huggingface_registry=HuggingFaceRegistryAdapter(processors),
            image=ImageAdapter(processors),
            login_client_type=LoginClientTypeAdapter(processors),
            login_history=LoginHistoryAdapter(processors),
            login_session=LoginSessionAdapter(processors),
            notification=NotificationAdapter(processors),
            object_storage=ObjectStorageAdapter(processors),
            project=ProjectAdapter(processors),
            prometheus_query_preset=PrometheusQueryPresetAdapter(processors),
            prometheus_query_preset_category=PrometheusQueryPresetCategoryAdapter(processors),
            rbac=RBACAdapter(processors),
            reservoir_registry=ReservoirRegistryAdapter(processors),
            resource_allocation=ResourceAllocationAdapter(processors, config_provider),
            resource_group=ResourceGroupAdapter(
                processors, deployment_coordinator, schedule_coordinator
            ),
            resource_policy=ResourcePolicyAdapter(processors),
            resource_preset=ResourcePresetAdapter(processors),
            resource_slot=ResourceSlotAdapter(processors),
            retention_policy=RetentionPolicyAdapter(processors),
            runtime_variant=RuntimeVariantAdapter(processors),
            runtime_variant_preset=RuntimeVariantPresetAdapter(processors),
            deployment_revision_preset=DeploymentRevisionPresetAdapter(processors),
            model_card=ModelCardAdapter(processors),
            resource_usage=ResourceUsageAdapter(processors),
            role_preset=RolePresetAdapter(processors),
            scheduling_handler=SchedulingHandlerAdapter(deployment_coordinator),
            scheduling_history=SchedulingHistoryAdapter(processors),
            service_catalog=ServiceCatalogAdapter(processors),
            session=SessionAdapter(processors),
            storage_host=StorageHostAdapter(processors),
            storage_namespace=StorageNamespaceAdapter(processors),
            user=UserAdapter(processors, auth_config),
            vfolder=VFolderAdapter(processors),
            vfs_storage=VFSStorageAdapter(processors),
        )

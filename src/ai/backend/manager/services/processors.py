from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

# fmt: off
if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager  # pants: no-infer-dep
    from ai.backend.common.clients.prometheus.client import PrometheusClient  # pants: no-infer-dep
    from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
        ValkeyArtifactDownloadTrackingClient,  # pants: no-infer-dep
    )
    from ai.backend.common.clients.valkey_client.valkey_live.client import (
        ValkeyLiveClient,  # pants: no-infer-dep
    )
    from ai.backend.common.clients.valkey_client.valkey_stat.client import (
        ValkeyStatClient,  # pants: no-infer-dep
    )
    from ai.backend.common.etcd import AsyncEtcd  # pants: no-infer-dep
    from ai.backend.common.events.dispatcher import (
        EventDispatcher,  # pants: no-infer-dep
        EventProducer,  # pants: no-infer-dep
    )
    from ai.backend.common.events.fetcher import EventFetcher  # pants: no-infer-dep
    from ai.backend.common.events.hub.hub import EventHub  # pants: no-infer-dep
    from ai.backend.common.plugin.hook import HookPluginContext  # pants: no-infer-dep
    from ai.backend.common.plugin.monitor import ErrorPluginContext  # pants: no-infer-dep
    from ai.backend.manager.agent_cache import AgentRPCCache  # pants: no-infer-dep
    from ai.backend.manager.clients.appproxy.client import AppProxyClientPool  # pants: no-infer-dep
    from ai.backend.manager.config.provider import ManagerConfigProvider  # pants: no-infer-dep
    from ai.backend.manager.idle import IdleCheckerHost  # pants: no-infer-dep
    from ai.backend.manager.models.storage import StorageSessionManager  # pants: no-infer-dep
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine  # pants: no-infer-dep
    from ai.backend.manager.notification import NotificationCenter  # pants: no-infer-dep
    from ai.backend.manager.registry import AgentRegistry  # pants: no-infer-dep
    from ai.backend.manager.repositories.repositories import Repositories  # pants: no-infer-dep
    from ai.backend.manager.service.container_registry.harbor import (
        AbstractPerProjectContainerRegistryQuotaService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.agent.processors import AgentProcessors  # pants: no-infer-dep
    from ai.backend.manager.services.agent.service import AgentService  # pants: no-infer-dep
    from ai.backend.manager.services.app_config.processors import (
        AppConfigProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.app_config.service import (
        AppConfigService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.artifact.processors import (
        ArtifactProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.artifact.service import ArtifactService  # pants: no-infer-dep
    from ai.backend.manager.services.artifact_registry.processors import (
        ArtifactRegistryProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.artifact_registry.service import (
        ArtifactRegistryService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.artifact_revision.processors import (
        ArtifactRevisionProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.artifact_revision.service import (
        ArtifactRevisionService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.audit_log.processors import (
        AuditLogProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.audit_log.service import AuditLogService  # pants: no-infer-dep
    from ai.backend.manager.services.auth.processors import AuthProcessors  # pants: no-infer-dep
    from ai.backend.manager.services.auth.service import AuthService  # pants: no-infer-dep
    from ai.backend.manager.services.container_registry.processors import (
        ContainerRegistryProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.container_registry.service import (
        ContainerRegistryService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.deployment.processors import (
        DeploymentProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.deployment.service import (
        DeploymentService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.domain.processors import (
        DomainProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.domain.service import DomainService  # pants: no-infer-dep
    from ai.backend.manager.services.dotfile.processors import (
        DotfileProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.dotfile.service import DotfileService  # pants: no-infer-dep
    from ai.backend.manager.services.error_log.processors import (
        ErrorLogProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.error_log.service import ErrorLogService  # pants: no-infer-dep
    from ai.backend.manager.services.etcd_config.processors import (
        EtcdConfigProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.etcd_config.service import (
        EtcdConfigService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.events.processors import (
        EventsProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.events.service import EventsService  # pants: no-infer-dep
    from ai.backend.manager.services.export.processors import (
        ExportProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.export.service import ExportService  # pants: no-infer-dep
    from ai.backend.manager.services.fair_share.processors import (
        FairShareProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.fair_share.service import (
        FairShareService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.group.processors import GroupProcessors  # pants: no-infer-dep
    from ai.backend.manager.services.group.service import GroupService  # pants: no-infer-dep
    from ai.backend.manager.services.image.processors import ImageProcessors  # pants: no-infer-dep
    from ai.backend.manager.services.image.service import ImageService  # pants: no-infer-dep
    from ai.backend.manager.services.keypair_resource_policy.processors import (
        KeypairResourcePolicyProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.keypair_resource_policy.service import (
        KeypairResourcePolicyService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.manager_admin.processors import (
        ManagerAdminProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.manager_admin.service import (
        ManagerAdminService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.metric.processors.utilization_metric import (
        UtilizationMetricProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.metric.root_service import (
        UtilizationMetricService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.model_serving.processors.auto_scaling import (
        ModelServingAutoScalingProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.model_serving.processors.model_serving import (
        ModelServingProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.model_serving.services.auto_scaling import (
        AutoScalingService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.model_serving.services.model_serving import (
        ModelServingService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.notification.processors import (
        NotificationProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.notification.service import (
        NotificationService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.object_storage.processors import (
        ObjectStorageProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.object_storage.service import (
        ObjectStorageService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.permission_contoller.processors import (
        PermissionControllerProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.permission_contoller.service import (
        PermissionControllerService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.project_resource_policy.processors import (
        ProjectResourcePolicyProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.project_resource_policy.service import (
        ProjectResourcePolicyService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.prometheus_query_preset.processors import (
        PrometheusQueryPresetProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.prometheus_query_preset.service import (
        PrometheusQueryPresetService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_preset.processors import (
        ResourcePresetProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_preset.service import (
        ResourcePresetService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_slot.processors import (
        ResourceSlotProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_slot.service import (
        ResourceSlotService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_usage.processors import (
        ResourceUsageProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.resource_usage.service import (
        ResourceUsageService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.scaling_group.processors import (
        ScalingGroupProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.scaling_group.service import (
        ScalingGroupService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.scheduling_history.processors import (
        SchedulingHistoryProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.scheduling_history.service import (
        SchedulingHistoryService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.service_catalog.processors import (
        ServiceCatalogProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.service_catalog.service import (
        ServiceCatalogService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.session.processors import (
        SessionProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.session.service import SessionService  # pants: no-infer-dep
    from ai.backend.manager.services.storage_namespace.processors import (
        StorageNamespaceProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.storage_namespace.service import (
        StorageNamespaceService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.stream.processors import (
        StreamProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.stream.service import StreamService  # pants: no-infer-dep
    from ai.backend.manager.services.template.processors import (
        TemplateProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.template.service import TemplateService  # pants: no-infer-dep
    from ai.backend.manager.services.user.processors import UserProcessors  # pants: no-infer-dep
    from ai.backend.manager.services.user.service import UserService  # pants: no-infer-dep
    from ai.backend.manager.services.user_resource_policy.processors import (
        UserResourcePolicyProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.user_resource_policy.service import (
        UserResourcePolicyService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfolder.processors import (
        VFolderFileProcessors,  # pants: no-infer-dep
        VFolderInviteProcessors,  # pants: no-infer-dep
        VFolderProcessors,  # pants: no-infer-dep
        VFolderSharingProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfolder.services.file import (
        VFolderFileService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfolder.services.invite import (
        VFolderInviteService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfolder.services.sharing import (
        VFolderSharingService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfolder.services.vfolder import (
        VFolderService,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfs_storage.processors import (
        VFSStorageProcessors,  # pants: no-infer-dep
    )
    from ai.backend.manager.services.vfs_storage.service import (
        VFSStorageService,  # pants: no-infer-dep
    )
    from ai.backend.manager.sokovan.deployment import DeploymentController  # pants: no-infer-dep
    from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
        RevisionGeneratorRegistry,  # pants: no-infer-dep
    )
    from ai.backend.manager.sokovan.scheduling_controller import (
        SchedulingController,  # pants: no-infer-dep
    )
# fmt: on


@dataclass
class ServiceArgs:
    db: ExtendedAsyncSAEngine
    repositories: Repositories
    etcd: AsyncEtcd
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    valkey_stat_client: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_artifact_client: ValkeyArtifactDownloadTrackingClient
    event_fetcher: EventFetcher
    background_task_manager: BackgroundTaskManager
    event_hub: EventHub
    agent_registry: AgentRegistry
    error_monitor: ErrorPluginContext
    idle_checker_host: IdleCheckerHost
    event_dispatcher: EventDispatcher
    hook_plugin_ctx: HookPluginContext
    scheduling_controller: SchedulingController
    deployment_controller: DeploymentController
    revision_generator_registry: RevisionGeneratorRegistry
    event_producer: EventProducer
    agent_cache: AgentRPCCache
    notification_center: NotificationCenter
    appproxy_client_pool: AppProxyClientPool
    prometheus_client: PrometheusClient
    registry_quota_service: AbstractPerProjectContainerRegistryQuotaService | None = None


@dataclass
class Services:
    agent: AgentService
    app_config: AppConfigService
    domain: DomainService
    dotfile: DotfileService
    error_log: ErrorLogService
    etcd_config: EtcdConfigService
    export: ExportService
    fair_share: FairShareService
    group: GroupService
    user: UserService
    image: ImageService
    container_registry: ContainerRegistryService
    vfolder: VFolderService
    vfolder_file: VFolderFileService
    vfolder_invite: VFolderInviteService
    vfolder_sharing: VFolderSharingService
    session: SessionService
    keypair_resource_policy: KeypairResourcePolicyService
    manager_admin: ManagerAdminService
    user_resource_policy: UserResourcePolicyService
    project_resource_policy: ProjectResourcePolicyService
    prometheus_query_preset: PrometheusQueryPresetService
    resource_preset: ResourcePresetService
    resource_slot: ResourceSlotService
    resource_usage: ResourceUsageService
    scaling_group: ScalingGroupService
    utilization_metric: UtilizationMetricService
    model_serving: ModelServingService
    model_serving_auto_scaling: AutoScalingService
    auth: AuthService
    notification: NotificationService
    object_storage: ObjectStorageService
    permission_controller: PermissionControllerService
    vfs_storage: VFSStorageService
    artifact: ArtifactService
    artifact_revision: ArtifactRevisionService
    artifact_registry: ArtifactRegistryService
    deployment: DeploymentService
    storage_namespace: StorageNamespaceService
    audit_log: AuditLogService
    scheduling_history: SchedulingHistoryService
    service_catalog: ServiceCatalogService
    template: TemplateService
    stream: StreamService
    events: EventsService


@dataclass
class ProcessorArgs:
    service_args: ServiceArgs
    event_hub: EventHub
    event_fetcher: EventFetcher


@dataclass
class Processors(AbstractProcessorPackage):
    agent: AgentProcessors
    app_config: AppConfigProcessors
    domain: DomainProcessors
    dotfile: DotfileProcessors
    error_log: ErrorLogProcessors
    etcd_config: EtcdConfigProcessors
    export: ExportProcessors
    fair_share: FairShareProcessors
    group: GroupProcessors
    user: UserProcessors
    image: ImageProcessors
    vfolder: VFolderProcessors
    vfolder_invite: VFolderInviteProcessors
    vfolder_sharing: VFolderSharingProcessors
    vfolder_file: VFolderFileProcessors
    session: SessionProcessors
    container_registry: ContainerRegistryProcessors
    keypair_resource_policy: KeypairResourcePolicyProcessors
    manager_admin: ManagerAdminProcessors
    user_resource_policy: UserResourcePolicyProcessors
    project_resource_policy: ProjectResourcePolicyProcessors
    prometheus_query_preset: PrometheusQueryPresetProcessors
    resource_preset: ResourcePresetProcessors
    resource_slot: ResourceSlotProcessors
    resource_usage: ResourceUsageProcessors
    scaling_group: ScalingGroupProcessors
    utilization_metric: UtilizationMetricProcessors
    model_serving: ModelServingProcessors
    model_serving_auto_scaling: ModelServingAutoScalingProcessors
    auth: AuthProcessors
    notification: NotificationProcessors
    object_storage: ObjectStorageProcessors
    permission_controller: PermissionControllerProcessors
    vfs_storage: VFSStorageProcessors
    artifact: ArtifactProcessors
    artifact_registry: ArtifactRegistryProcessors
    artifact_revision: ArtifactRevisionProcessors
    deployment: DeploymentProcessors
    storage_namespace: StorageNamespaceProcessors
    audit_log: AuditLogProcessors
    scheduling_history: SchedulingHistoryProcessors
    service_catalog: ServiceCatalogProcessors
    template: TemplateProcessors
    stream: StreamProcessors
    events: EventsProcessors

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            *self.agent.supported_actions(),
            *self.app_config.supported_actions(),
            *self.domain.supported_actions(),
            *self.dotfile.supported_actions(),
            *self.error_log.supported_actions(),
            *self.etcd_config.supported_actions(),
            *self.export.supported_actions(),
            *self.fair_share.supported_actions(),
            *self.group.supported_actions(),
            *self.user.supported_actions(),
            *self.image.supported_actions(),
            *self.container_registry.supported_actions(),
            *self.vfolder.supported_actions(),
            *self.vfolder_file.supported_actions(),
            *self.vfolder_invite.supported_actions(),
            *self.vfolder_sharing.supported_actions(),
            *self.session.supported_actions(),
            *self.keypair_resource_policy.supported_actions(),
            *self.manager_admin.supported_actions(),
            *self.user_resource_policy.supported_actions(),
            *self.project_resource_policy.supported_actions(),
            *self.prometheus_query_preset.supported_actions(),
            *self.resource_preset.supported_actions(),
            *self.resource_slot.supported_actions(),
            *self.resource_usage.supported_actions(),
            *self.scaling_group.supported_actions(),
            *self.utilization_metric.supported_actions(),
            *self.model_serving.supported_actions(),
            *self.model_serving_auto_scaling.supported_actions(),
            *self.auth.supported_actions(),
            *self.notification.supported_actions(),
            *self.object_storage.supported_actions(),
            *self.permission_controller.supported_actions(),
            *self.vfs_storage.supported_actions(),
            *self.artifact_registry.supported_actions(),
            *self.artifact_revision.supported_actions(),
            *self.artifact.supported_actions(),
            *self.deployment.supported_actions(),
            *self.storage_namespace.supported_actions(),
            *self.audit_log.supported_actions(),
            *self.scheduling_history.supported_actions(),
            *self.service_catalog.supported_actions(),
            *self.template.supported_actions(),
            *self.stream.supported_actions(),
            *self.events.supported_actions(),
        ]

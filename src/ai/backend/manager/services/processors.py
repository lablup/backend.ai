from dataclasses import dataclass
from typing import Self, override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.notification import NotificationCenter
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.service.container_registry.harbor import (
    AbstractPerProjectContainerRegistryQuotaService,
)
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.app_config.service import AppConfigService
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors
from ai.backend.manager.services.audit_log.service import AuditLogService
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.dotfile.processors import DotfileProcessors
from ai.backend.manager.services.dotfile.service import DotfileService
from ai.backend.manager.services.error_log.processors import ErrorLogProcessors
from ai.backend.manager.services.error_log.service import ErrorLogService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService
from ai.backend.manager.services.events.processors import EventsProcessors
from ai.backend.manager.services.events.service import EventsService
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.keypair_resource_policy.service import KeypairResourcePolicyService
from ai.backend.manager.services.manager_admin.processors import ManagerAdminProcessors
from ai.backend.manager.services.manager_admin.service import ManagerAdminService
from ai.backend.manager.services.metric.processors.utilization_metric import (
    UtilizationMetricProcessors,
)
from ai.backend.manager.services.metric.root_service import UtilizationMetricService
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.services.model_serving.services.model_serving import (
    ModelServingService,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.notification.service import NotificationService
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.resource_slot.service import ResourceSlotService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.manager.services.resource_usage.service import ResourceUsageService
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService
from ai.backend.manager.services.service_catalog.processors import ServiceCatalogProcessors
from ai.backend.manager.services.service_catalog.service import ServiceCatalogService
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService
from ai.backend.manager.services.stream.processors import StreamProcessors
from ai.backend.manager.services.stream.service import StreamService
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService
from ai.backend.manager.services.vfolder.processors import (
    VFolderFileProcessors,
    VFolderInviteProcessors,
    VFolderProcessors,
    VFolderSharingProcessors,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.services.vfs_storage.service import VFSStorageService
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


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

    @classmethod
    def create(cls, args: ServiceArgs) -> Self:
        repositories = args.repositories
        agent_service = AgentService(
            args.etcd,
            args.agent_registry,
            args.config_provider,
            repositories.agent.repository,
            repositories.scheduler.repository,
            args.hook_plugin_ctx,
            args.event_producer,
            args.agent_cache,
        )
        app_config_service = AppConfigService(
            app_config_repository=repositories.app_config.repository,
        )
        domain_service = DomainService(repositories.domain.repository)
        dotfile_service = DotfileService(
            repository=repositories.dotfile.repository,
        )
        error_log_service = ErrorLogService(
            repository=repositories.error_log.repository,
        )
        etcd_config_service = EtcdConfigService(
            repository=repositories.etcd_config.repository,
            config_provider=args.config_provider,
            etcd=args.etcd,
            valkey_stat=args.valkey_stat_client,
        )
        export_service = ExportService(
            repository=repositories.export.repository,
        )
        fair_share_service = FairShareService(
            repository=repositories.fair_share.repository,
        )
        group_service = GroupService(
            args.storage_manager,
            args.config_provider,
            args.valkey_stat_client,
            repositories.group,
        )
        user_service = UserService(
            args.storage_manager,
            args.valkey_stat_client,
            args.agent_registry,
            repositories.user.repository,
        )
        image_service = ImageService(
            args.agent_registry, repositories.image.repository, args.config_provider
        )
        container_registry_service = ContainerRegistryService(
            args.db,
            repositories.container_registry.repository,
            quota_service=args.registry_quota_service,
        )
        vfolder_service = VFolderService(
            args.config_provider,
            args.etcd,
            args.storage_manager,
            args.background_task_manager,
            repositories.vfolder.repository,
            repositories.user.repository,
            args.valkey_stat_client,
        )
        vfolder_file_service = VFolderFileService(
            args.config_provider,
            args.storage_manager,
            repositories.vfolder.repository,
            repositories.user.repository,
        )
        vfolder_invite_service = VFolderInviteService(
            args.config_provider,
            repositories.vfolder.repository,
            repositories.user.repository,
        )
        vfolder_sharing_service = VFolderSharingService(
            args.config_provider,
            repositories.vfolder.repository,
            repositories.user.repository,
        )
        session_service = SessionService(
            SessionServiceArgs(
                agent_registry=args.agent_registry,
                event_fetcher=args.event_fetcher,
                background_task_manager=args.background_task_manager,
                event_hub=args.event_hub,
                error_monitor=args.error_monitor,
                idle_checker_host=args.idle_checker_host,
                session_repository=repositories.session.repository,
                scheduling_controller=args.scheduling_controller,
                appproxy_client_pool=args.appproxy_client_pool,
            )
        )
        keypair_resource_policy_service = KeypairResourcePolicyService(
            repositories.keypair_resource_policy.repository
        )
        manager_admin_service = ManagerAdminService(
            repository=repositories.manager_admin.repository,
            config_provider=args.config_provider,
            etcd=args.etcd,
            db=args.db,
            valkey_stat=args.valkey_stat_client,
        )
        user_resource_policy_service = UserResourcePolicyService(
            repositories.user_resource_policy.repository
        )
        project_resource_policy_service = ProjectResourcePolicyService(
            repositories.project_resource_policy.repository
        )
        prometheus_query_preset_service = PrometheusQueryPresetService(
            repository=repositories.prometheus_query_preset.repository,
            prometheus_client=args.prometheus_client,
            default_timewindow=args.config_provider.config.metric.timewindow,
        )
        resource_preset_service = ResourcePresetService(
            repositories.resource_preset.repository,
        )
        resource_slot_service = ResourceSlotService(repositories.resource_slot.repository)
        resource_usage_service = ResourceUsageService(
            repository=repositories.resource_usage_history.repository,
        )
        scaling_group_service = ScalingGroupService(
            repositories.scaling_group.repository,
            appproxy_client_pool=args.appproxy_client_pool,
        )
        utilization_metric_service = UtilizationMetricService(
            args.prometheus_client,
            args.config_provider.config.metric.timewindow,
            repositories.metric.repository,
        )

        # Use deployment-based model serving if deployment_controller is available
        model_serving_service = ModelServingService(
            agent_registry=args.agent_registry,
            background_task_manager=args.background_task_manager,
            event_dispatcher=args.event_dispatcher,
            event_hub=args.event_hub,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
            valkey_live=args.valkey_live,
            repository=repositories.model_serving.repository,
            deployment_repository=args.deployment_controller._deployment_repository,
            deployment_controller=args.deployment_controller,
            scheduling_controller=args.scheduling_controller,
            revision_generator_registry=args.revision_generator_registry,
        )

        model_serving_auto_scaling = AutoScalingService(
            repository=repositories.model_serving.repository,
        )
        auth = AuthService(
            hook_plugin_ctx=args.hook_plugin_ctx,
            auth_repository=repositories.auth.repository,
            config_provider=args.config_provider,
        )
        notification_service = NotificationService(
            repository=repositories.notification.repository,
            notification_center=args.notification_center,
        )
        permission_controller_service = PermissionControllerService(
            repository=repositories.permission_controller.repository,
        )
        object_storage_service = ObjectStorageService(
            artifact_repository=repositories.artifact.repository,
            object_storage_repository=repositories.object_storage.repository,
            storage_namespace_repository=repositories.storage_namespace.repository,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
        )
        vfs_storage_service = VFSStorageService(
            vfs_storage_repository=repositories.vfs_storage.repository,
            storage_manager=args.storage_manager,
        )
        artifact_service = ArtifactService(
            artifact_repository=repositories.artifact.repository,
            artifact_registry_repository=repositories.artifact_registry.repository,
            storage_manager=args.storage_manager,
            object_storage_repository=repositories.object_storage.repository,
            vfs_storage_repository=repositories.vfs_storage.repository,
            huggingface_registry_repository=repositories.huggingface_registry.repository,
            config_provider=args.config_provider,
            reservoir_registry_repository=repositories.reservoir_registry.repository,
        )
        artifact_revision_service = ArtifactRevisionService(
            artifact_repository=repositories.artifact.repository,
            artifact_registry_repository=repositories.artifact_registry.repository,
            storage_manager=args.storage_manager,
            object_storage_repository=repositories.object_storage.repository,
            vfs_storage_repository=repositories.vfs_storage.repository,
            storage_namespace_repository=repositories.storage_namespace.repository,
            huggingface_registry_repository=repositories.huggingface_registry.repository,
            reservoir_registry_repository=repositories.reservoir_registry.repository,
            vfolder_repository=repositories.vfolder.repository,
            config_provider=args.config_provider,
            valkey_artifact_client=args.valkey_artifact_client,
            background_task_manager=args.background_task_manager,
        )
        artifact_registry_service = ArtifactRegistryService(
            repositories.huggingface_registry.repository,
            repositories.reservoir_registry.repository,
            repositories.artifact_registry.repository,
        )
        deployment_service = DeploymentService(
            args.deployment_controller,
            args.deployment_controller._deployment_repository,
        )
        storage_namespace_service = StorageNamespaceService(
            repositories.storage_namespace.repository
        )
        audit_log_service = AuditLogService(repositories.audit_log.repository)
        scheduling_history_service = SchedulingHistoryService(
            repositories.scheduling_history.repository
        )
        service_catalog_service = ServiceCatalogService(args.db)
        template_service = TemplateService(
            repository=repositories.template.repository,
        )
        stream_service = StreamService(
            repository=repositories.stream.repository,
            registry=args.agent_registry,
            valkey_live=args.valkey_live,
            idle_checker_host=args.idle_checker_host,
            etcd=args.etcd,
        )
        events_service = EventsService(
            repository=repositories.events.repository,
            db=args.db,
        )

        return cls(
            agent=agent_service,
            app_config=app_config_service,
            domain=domain_service,
            dotfile=dotfile_service,
            error_log=error_log_service,
            etcd_config=etcd_config_service,
            export=export_service,
            fair_share=fair_share_service,
            group=group_service,
            user=user_service,
            image=image_service,
            container_registry=container_registry_service,
            vfolder=vfolder_service,
            vfolder_file=vfolder_file_service,
            vfolder_invite=vfolder_invite_service,
            vfolder_sharing=vfolder_sharing_service,
            session=session_service,
            keypair_resource_policy=keypair_resource_policy_service,
            manager_admin=manager_admin_service,
            user_resource_policy=user_resource_policy_service,
            project_resource_policy=project_resource_policy_service,
            prometheus_query_preset=prometheus_query_preset_service,
            resource_preset=resource_preset_service,
            resource_slot=resource_slot_service,
            resource_usage=resource_usage_service,
            scaling_group=scaling_group_service,
            utilization_metric=utilization_metric_service,
            model_serving=model_serving_service,
            model_serving_auto_scaling=model_serving_auto_scaling,
            auth=auth,
            notification=notification_service,
            object_storage=object_storage_service,
            permission_controller=permission_controller_service,
            vfs_storage=vfs_storage_service,
            artifact=artifact_service,
            artifact_revision=artifact_revision_service,
            artifact_registry=artifact_registry_service,
            deployment=deployment_service,
            storage_namespace=storage_namespace_service,
            audit_log=audit_log_service,
            scheduling_history=scheduling_history_service,
            service_catalog=service_catalog_service,
            template=template_service,
            stream=stream_service,
            events=events_service,
        )


@dataclass
class ProcessorArgs:
    service_args: ServiceArgs


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

    @classmethod
    def create(cls, args: ProcessorArgs, action_monitors: list[ActionMonitor]) -> Self:
        services = Services.create(args.service_args)
        agent_processors = AgentProcessors(services.agent, action_monitors)
        app_config_processors = AppConfigProcessors(services.app_config, action_monitors)
        domain_processors = DomainProcessors(services.domain, action_monitors)
        dotfile_processors = DotfileProcessors(services.dotfile, action_monitors)
        error_log_processors = ErrorLogProcessors(services.error_log, action_monitors)
        etcd_config_processors = EtcdConfigProcessors(services.etcd_config, action_monitors)
        export_processors = ExportProcessors(services.export, action_monitors)
        fair_share_processors = FairShareProcessors(services.fair_share, action_monitors)
        group_processors = GroupProcessors(services.group, action_monitors)
        user_processors = UserProcessors(services.user, action_monitors)
        image_processors = ImageProcessors(services.image, action_monitors)
        container_registry_processors = ContainerRegistryProcessors(
            services.container_registry, action_monitors
        )
        vfolder_processors = VFolderProcessors(services.vfolder, action_monitors)
        vfolder_file_processors = VFolderFileProcessors(services.vfolder_file, action_monitors)
        vfolder_invite_processors = VFolderInviteProcessors(
            services.vfolder_invite, action_monitors
        )
        vfolder_sharing_processors = VFolderSharingProcessors(
            services.vfolder_sharing, action_monitors
        )
        session_processors = SessionProcessors(services.session, action_monitors)
        keypair_resource_policy_processors = KeypairResourcePolicyProcessors(
            services.keypair_resource_policy, action_monitors
        )
        manager_admin_processors = ManagerAdminProcessors(services.manager_admin, action_monitors)
        user_resource_policy_processors = UserResourcePolicyProcessors(
            services.user_resource_policy, action_monitors
        )
        project_resource_policy_processors = ProjectResourcePolicyProcessors(
            services.project_resource_policy, action_monitors
        )
        prometheus_query_preset_processors = PrometheusQueryPresetProcessors(
            services.prometheus_query_preset, action_monitors
        )
        resource_preset_processors = ResourcePresetProcessors(
            services.resource_preset, action_monitors
        )
        resource_slot_processors = ResourceSlotProcessors(services.resource_slot, action_monitors)
        resource_usage_processors = ResourceUsageProcessors(
            services.resource_usage, action_monitors
        )
        scaling_group_processors = ScalingGroupProcessors(services.scaling_group, action_monitors)
        model_serving_processors = ModelServingProcessors(services.model_serving, action_monitors)
        model_serving_auto_scaling_processors = ModelServingAutoScalingProcessors(
            services.model_serving_auto_scaling, action_monitors
        )
        utilization_metric_processors = UtilizationMetricProcessors(
            services.utilization_metric, action_monitors
        )
        auth = AuthProcessors(services.auth, action_monitors)
        notification_processors = NotificationProcessors(services.notification, action_monitors)
        permission_controller_processors = PermissionControllerProcessors(
            services.permission_controller, action_monitors
        )
        object_storage_processors = ObjectStorageProcessors(
            services.object_storage, action_monitors
        )
        vfs_storage_processors = VFSStorageProcessors(services.vfs_storage, action_monitors)
        artifact_processors = ArtifactProcessors(services.artifact, action_monitors)
        artifact_registry_processors = ArtifactRegistryProcessors(
            services.artifact_registry, action_monitors
        )
        artifact_revision_processors = ArtifactRevisionProcessors(
            services.artifact_revision, action_monitors
        )

        deployment_processors = DeploymentProcessors(services.deployment, action_monitors)

        storage_namespace_processors = StorageNamespaceProcessors(
            services.storage_namespace, action_monitors
        )
        audit_log_processors = AuditLogProcessors(services.audit_log, [])
        scheduling_history_processors = SchedulingHistoryProcessors(
            services.scheduling_history, action_monitors
        )
        service_catalog_processors = ServiceCatalogProcessors(
            services.service_catalog, action_monitors
        )
        template_processors = TemplateProcessors(services.template, action_monitors)
        stream_processors = StreamProcessors(services.stream, action_monitors)
        events_processors = EventsProcessors(services.events, action_monitors)

        return cls(
            agent=agent_processors,
            app_config=app_config_processors,
            domain=domain_processors,
            dotfile=dotfile_processors,
            error_log=error_log_processors,
            etcd_config=etcd_config_processors,
            export=export_processors,
            fair_share=fair_share_processors,
            group=group_processors,
            user=user_processors,
            image=image_processors,
            container_registry=container_registry_processors,
            vfolder=vfolder_processors,
            vfolder_file=vfolder_file_processors,
            vfolder_invite=vfolder_invite_processors,
            vfolder_sharing=vfolder_sharing_processors,
            session=session_processors,
            keypair_resource_policy=keypair_resource_policy_processors,
            manager_admin=manager_admin_processors,
            user_resource_policy=user_resource_policy_processors,
            project_resource_policy=project_resource_policy_processors,
            prometheus_query_preset=prometheus_query_preset_processors,
            resource_preset=resource_preset_processors,
            resource_slot=resource_slot_processors,
            resource_usage=resource_usage_processors,
            scaling_group=scaling_group_processors,
            utilization_metric=utilization_metric_processors,
            model_serving=model_serving_processors,
            model_serving_auto_scaling=model_serving_auto_scaling_processors,
            auth=auth,
            notification=notification_processors,
            object_storage=object_storage_processors,
            permission_controller=permission_controller_processors,
            vfs_storage=vfs_storage_processors,
            artifact=artifact_processors,
            artifact_registry=artifact_registry_processors,
            artifact_revision=artifact_revision_processors,
            deployment=deployment_processors,
            storage_namespace=storage_namespace_processors,
            audit_log=audit_log_processors,
            scheduling_history=scheduling_history_processors,
            service_catalog=service_catalog_processors,
            template=template_processors,
            stream=stream_processors,
            events=events_processors,
        )

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
            *(self.deployment.supported_actions() if self.deployment else []),
            *self.storage_namespace.supported_actions(),
            *self.audit_log.supported_actions(),
            *self.scheduling_history.supported_actions(),
            *self.service_catalog.supported_actions(),
            *self.template.supported_actions(),
            *self.stream.supported_actions(),
            *self.events.supported_actions(),
        ]

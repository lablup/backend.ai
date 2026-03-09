from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validators import ActionValidators
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
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs, Services
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


def create_services(args: ServiceArgs) -> Services:
    repositories = args.repositories
    return Services(
        agent=AgentService(
            args.etcd,
            args.agent_registry,
            args.config_provider,
            repositories.agent.repository,
            repositories.scheduler.repository,
            args.hook_plugin_ctx,
            args.event_producer,
            args.agent_cache,
        ),
        app_config=AppConfigService(
            app_config_repository=repositories.app_config.repository,
        ),
        domain=DomainService(repositories.domain.repository),
        dotfile=DotfileService(
            repository=repositories.dotfile.repository,
        ),
        error_log=ErrorLogService(
            repository=repositories.error_log.repository,
        ),
        etcd_config=EtcdConfigService(
            repository=repositories.etcd_config.repository,
            config_provider=args.config_provider,
            etcd=args.etcd,
            valkey_stat=args.valkey_stat_client,
        ),
        export=ExportService(
            repository=repositories.export.repository,
        ),
        fair_share=FairShareService(
            repository=repositories.fair_share.repository,
        ),
        group=GroupService(
            args.storage_manager,
            args.config_provider,
            args.valkey_stat_client,
            repositories.group,
        ),
        user=UserService(
            args.storage_manager,
            args.valkey_stat_client,
            args.agent_registry,
            repositories.user.repository,
        ),
        image=ImageService(
            args.agent_registry, repositories.image.repository, args.config_provider
        ),
        container_registry=ContainerRegistryService(
            args.db,
            repositories.container_registry.repository,
            quota_service=args.registry_quota_service,
        ),
        vfolder=VFolderService(
            args.config_provider,
            args.etcd,
            args.storage_manager,
            args.background_task_manager,
            repositories.vfolder.repository,
            repositories.user.repository,
            args.valkey_stat_client,
        ),
        vfolder_file=VFolderFileService(
            args.config_provider,
            args.storage_manager,
            repositories.vfolder.repository,
            repositories.user.repository,
        ),
        vfolder_invite=VFolderInviteService(
            args.config_provider,
            repositories.vfolder.repository,
            repositories.user.repository,
        ),
        vfolder_sharing=VFolderSharingService(
            args.config_provider,
            repositories.vfolder.repository,
            repositories.user.repository,
        ),
        session=SessionService(
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
        ),
        keypair_resource_policy=KeypairResourcePolicyService(
            repositories.keypair_resource_policy.repository
        ),
        manager_admin=ManagerAdminService(
            repository=repositories.manager_admin.repository,
            config_provider=args.config_provider,
            etcd=args.etcd,
            db=args.db,
            valkey_stat=args.valkey_stat_client,
        ),
        user_resource_policy=UserResourcePolicyService(
            repositories.user_resource_policy.repository
        ),
        project_resource_policy=ProjectResourcePolicyService(
            repositories.project_resource_policy.repository
        ),
        prometheus_query_preset=PrometheusQueryPresetService(
            repository=repositories.prometheus_query_preset.repository,
            prometheus_client=args.prometheus_client,
            default_timewindow=args.config_provider.config.metric.timewindow,
        ),
        resource_preset=ResourcePresetService(
            repositories.resource_preset.repository,
        ),
        resource_slot=ResourceSlotService(repositories.resource_slot.repository),
        resource_usage=ResourceUsageService(
            repository=repositories.resource_usage_history.repository,
        ),
        scaling_group=ScalingGroupService(
            repositories.scaling_group.repository,
            appproxy_client_pool=args.appproxy_client_pool,
        ),
        utilization_metric=UtilizationMetricService(
            args.prometheus_client,
            args.config_provider.config.metric.timewindow,
            repositories.metric.repository,
        ),
        model_serving=ModelServingService(
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
        ),
        model_serving_auto_scaling=AutoScalingService(
            repository=repositories.model_serving.repository,
        ),
        auth=AuthService(
            hook_plugin_ctx=args.hook_plugin_ctx,
            auth_repository=repositories.auth.repository,
            config_provider=args.config_provider,
        ),
        notification=NotificationService(
            repository=repositories.notification.repository,
            notification_center=args.notification_center,
        ),
        object_storage=ObjectStorageService(
            artifact_repository=repositories.artifact.repository,
            object_storage_repository=repositories.object_storage.repository,
            storage_namespace_repository=repositories.storage_namespace.repository,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
        ),
        permission_controller=PermissionControllerService(
            repository=repositories.permission_controller.repository,
        ),
        vfs_storage=VFSStorageService(
            vfs_storage_repository=repositories.vfs_storage.repository,
            storage_manager=args.storage_manager,
        ),
        artifact=ArtifactService(
            artifact_repository=repositories.artifact.repository,
            artifact_registry_repository=repositories.artifact_registry.repository,
            storage_manager=args.storage_manager,
            object_storage_repository=repositories.object_storage.repository,
            vfs_storage_repository=repositories.vfs_storage.repository,
            huggingface_registry_repository=repositories.huggingface_registry.repository,
            config_provider=args.config_provider,
            reservoir_registry_repository=repositories.reservoir_registry.repository,
        ),
        artifact_revision=ArtifactRevisionService(
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
        ),
        artifact_registry=ArtifactRegistryService(
            repositories.huggingface_registry.repository,
            repositories.reservoir_registry.repository,
            repositories.artifact_registry.repository,
        ),
        deployment=DeploymentService(
            args.deployment_controller,
            args.deployment_controller._deployment_repository,
            args.revision_generator_registry,
        ),
        storage_namespace=StorageNamespaceService(repositories.storage_namespace.repository),
        audit_log=AuditLogService(repositories.audit_log.repository),
        scheduling_history=SchedulingHistoryService(repositories.scheduling_history.repository),
        service_catalog=ServiceCatalogService(args.db),
        template=TemplateService(
            repository=repositories.template.repository,
        ),
        stream=StreamService(
            repository=repositories.stream.repository,
            registry=args.agent_registry,
            valkey_live=args.valkey_live,
            idle_checker_host=args.idle_checker_host,
            etcd=args.etcd,
        ),
        events=EventsService(
            repository=repositories.events.repository,
            db=args.db,
        ),
    )


def create_processors(
    args: ProcessorArgs,
    action_monitors: list[ActionMonitor],
    validators: ActionValidators,
) -> Processors:
    services = create_services(args.service_args)
    return Processors(
        agent=AgentProcessors(services.agent, action_monitors, validators),
        app_config=AppConfigProcessors(services.app_config, action_monitors, validators),
        domain=DomainProcessors(services.domain, action_monitors, validators),
        dotfile=DotfileProcessors(services.dotfile, action_monitors, validators),
        error_log=ErrorLogProcessors(services.error_log, action_monitors, validators),
        etcd_config=EtcdConfigProcessors(services.etcd_config, action_monitors, validators),
        export=ExportProcessors(services.export, action_monitors, validators),
        fair_share=FairShareProcessors(services.fair_share, action_monitors, validators),
        group=GroupProcessors(services.group, action_monitors, validators),
        user=UserProcessors(services.user, action_monitors, validators),
        image=ImageProcessors(services.image, action_monitors, validators),
        container_registry=ContainerRegistryProcessors(
            services.container_registry, action_monitors, validators
        ),
        vfolder=VFolderProcessors(services.vfolder, action_monitors, validators),
        vfolder_file=VFolderFileProcessors(services.vfolder_file, action_monitors, validators),
        vfolder_invite=VFolderInviteProcessors(
            services.vfolder_invite, action_monitors, validators
        ),
        vfolder_sharing=VFolderSharingProcessors(
            services.vfolder_sharing, action_monitors, validators
        ),
        session=SessionProcessors(services.session, action_monitors, validators),
        keypair_resource_policy=KeypairResourcePolicyProcessors(
            services.keypair_resource_policy, action_monitors, validators
        ),
        manager_admin=ManagerAdminProcessors(services.manager_admin, action_monitors, validators),
        user_resource_policy=UserResourcePolicyProcessors(
            services.user_resource_policy, action_monitors, validators
        ),
        project_resource_policy=ProjectResourcePolicyProcessors(
            services.project_resource_policy, action_monitors, validators
        ),
        prometheus_query_preset=PrometheusQueryPresetProcessors(
            services.prometheus_query_preset, action_monitors, validators
        ),
        resource_preset=ResourcePresetProcessors(
            services.resource_preset, action_monitors, validators
        ),
        resource_slot=ResourceSlotProcessors(services.resource_slot, action_monitors, validators),
        resource_usage=ResourceUsageProcessors(
            services.resource_usage, action_monitors, validators
        ),
        scaling_group=ScalingGroupProcessors(services.scaling_group, action_monitors, validators),
        utilization_metric=UtilizationMetricProcessors(
            services.utilization_metric, action_monitors, validators
        ),
        model_serving=ModelServingProcessors(services.model_serving, action_monitors, validators),
        model_serving_auto_scaling=ModelServingAutoScalingProcessors(
            services.model_serving_auto_scaling, action_monitors, validators
        ),
        auth=AuthProcessors(services.auth, action_monitors, validators),
        notification=NotificationProcessors(services.notification, action_monitors, validators),
        object_storage=ObjectStorageProcessors(
            services.object_storage, action_monitors, validators
        ),
        permission_controller=PermissionControllerProcessors(
            services.permission_controller, action_monitors, validators
        ),
        vfs_storage=VFSStorageProcessors(services.vfs_storage, action_monitors, validators),
        artifact=ArtifactProcessors(services.artifact, action_monitors, validators),
        artifact_registry=ArtifactRegistryProcessors(
            services.artifact_registry, action_monitors, validators
        ),
        artifact_revision=ArtifactRevisionProcessors(
            services.artifact_revision, action_monitors, validators
        ),
        deployment=DeploymentProcessors(services.deployment, action_monitors, validators),
        storage_namespace=StorageNamespaceProcessors(
            services.storage_namespace, action_monitors, validators
        ),
        audit_log=AuditLogProcessors(services.audit_log, [], validators),
        scheduling_history=SchedulingHistoryProcessors(
            services.scheduling_history, action_monitors, validators
        ),
        service_catalog=ServiceCatalogProcessors(
            services.service_catalog, action_monitors, validators
        ),
        template=TemplateProcessors(services.template, action_monitors, validators),
        stream=StreamProcessors(services.stream, action_monitors),
        events=EventsProcessors(
            services.events,
            action_monitors,
            event_hub=args.event_hub,
            event_fetcher=args.event_fetcher,
        ),
    )

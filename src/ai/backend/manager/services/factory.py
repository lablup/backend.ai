from typing import Any

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.app_config import (
    APP_CONFIG_ALLOW_LIST_ENTITY_TYPE,
    APP_CONFIG_ENTITY_TYPE,
    APP_CONFIG_FRAGMENT_ENTITY_TYPE,
)
from ai.backend.common.data.entity.app_config_definition import APP_CONFIG_DEFINITION_ENTITY_TYPE
from ai.backend.common.data.entity.artifact import ARTIFACT_ENTITY_TYPE
from ai.backend.common.data.entity.artifact_registry import ARTIFACT_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.artifact_revision import ARTIFACT_REVISION_FIELD_TYPE
from ai.backend.common.data.entity.audit_log import AUDIT_LOG_FIELD_TYPE
from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.etcd_config import ETCD_CONFIG_ENTITY_TYPE
from ai.backend.common.data.entity.export import EXPORT_ENTITY_TYPE
from ai.backend.common.data.entity.fair_share import (
    DOMAIN_FAIR_SHARE_ENTITY_TYPE,
    PROJECT_FAIR_SHARE_ENTITY_TYPE,
    USER_FAIR_SHARE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.image import IMAGE_ENTITY_TYPE
from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NOTIFICATION_RULE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.runtime_variant_preset import RUNTIME_VARIANT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.service_catalog import SERVICE_CATALOG_ENTITY_TYPE
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.session_template import SESSION_TEMPLATE_ENTITY_TYPE
from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.usage_bucket import (
    DOMAIN_USAGE_BUCKET_FIELD_TYPE,
    PROJECT_USAGE_BUCKET_FIELD_TYPE,
    USER_USAGE_BUCKET_FIELD_TYPE,
)
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE
from ai.backend.common.data.entity.vfolder_invitation import VFOLDER_INVITATION_ENTITY_TYPE
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.action import RBAC_ACTION_REGISTRY
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.clients.prometheus.preset import PromQLTemplateRenderer
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.app_config.processors import (
    AppConfigProcessors,
)
from ai.backend.manager.services.app_config.service import (
    AppConfigService,
)
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.manager.services.artifact.revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact.revision.service import ArtifactRevisionService
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentPresetProcessors,
)
from ai.backend.manager.services.deployment_revision_preset.service import (
    DeploymentPresetService,
)
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService
from ai.backend.manager.services.events.service import EventsService
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.idle_checker.service import IdleCheckerService
from ai.backend.manager.services.idle_checker_assignment.processors import (
    IdleCheckerAssignmentProcessors,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.login_client_type.processors import (
    LoginClientTypeProcessors,
)
from ai.backend.manager.services.manager_admin.processors import ManagerAdminProcessors
from ai.backend.manager.services.manager_admin.service import ManagerAdminService
from ai.backend.manager.services.metric.processors import MetricProcessors
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_card.service import ModelCardService
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
from ai.backend.manager.services.processors import (
    ProcessorArgs,
    Processors,
    ProcessorsBundle,
    ServiceArgs,
    Services,
)
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)
from ai.backend.manager.services.prometheus_query_preset_category.processors import (
    PrometheusQueryPresetCategoryProcessors,
)
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.resource_slot.service import ResourceSlotService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.manager.services.retention_policy.processors import RetentionPolicyProcessors
from ai.backend.manager.services.role_preset.processors import RolePresetProcessors
from ai.backend.manager.services.role_preset.service import RolePresetService
from ai.backend.manager.services.runtime_variant.processors import RuntimeVariantProcessors
from ai.backend.manager.services.runtime_variant_preset.processors import (
    RuntimeVariantPresetProcessors,
)
from ai.backend.manager.services.runtime_variant_preset.service import RuntimeVariantPresetService
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService
from ai.backend.manager.services.service_catalog.processors import ServiceCatalogProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.resource_allocation.service import (
    ResourceAllocationService,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors
from ai.backend.manager.services.stream.processors import StreamProcessors
from ai.backend.manager.services.stream.service import StreamService
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.vfolder.processors import (
    VFolderFileProcessors,
    VFolderInviteProcessors,
    VFolderProcessors,
    VFolderSharingProcessors,
)
from ai.backend.manager.services.vfolder.processors.vfolder_admin import VFolderAdminProcessors
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.services.vfolder.services.vfolder_admin import VFolderAdminService
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
            args.scheduling_controller,
            args.hook_plugin_ctx,
            args.event_producer,
            args.agent_cache,
        ),
        app_config=AppConfigService(OpsRepository(repositories.v2_ops_provider)),
        domain=DomainService(repositories.domain.repository),
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
            args.scheduling_controller,
        ),
        idle_checker=IdleCheckerService(
            repositories.idle_checker.repository,
            repositories.prometheus_query_preset.repository,
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
        vfolder_admin=VFolderAdminService(
            vfolder_admin_repository=repositories.vfolder.admin_repository,
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
                scheduler_repository=repositories.scheduler.repository,
                scheduling_controller=args.scheduling_controller,
                appproxy_client_pool=args.appproxy_client_pool,
                user_repository=repositories.user.repository,
            )
        ),
        manager_admin=ManagerAdminService(
            repository=repositories.manager_admin.repository,
            config_provider=args.config_provider,
            etcd=args.etcd,
            db=args.db,
            valkey_stat=args.valkey_stat_client,
        ),
        prometheus_query_preset=PrometheusQueryPresetService(
            repository=repositories.prometheus_query_preset.repository,
            prometheus_client=args.prometheus_client,
            default_timewindow=args.config_provider.config.metric.timewindow,
            template_renderer=PromQLTemplateRenderer(),
            ops_repository=OpsRepository(repositories.v2_ops_provider),
        ),
        resource_preset=ResourcePresetService(
            repositories.resource_preset.repository,
        ),
        resource_slot=ResourceSlotService(repositories.resource_slot.repository),
        role_preset=RolePresetService(OpsRepository(repositories.v2_ops_provider)),
        runtime_variant_preset=RuntimeVariantPresetService(
            repositories.runtime_variant_preset.repository,
        ),
        deployment_revision_preset=DeploymentPresetService(
            repositories.deployment_revision_preset.repository,
        ),
        model_card=ModelCardService(
            repositories.model_card.repository,
            args.storage_manager,
        ),
        resource_group=ResourceGroupService(
            repositories.resource_group.repository,
            appproxy_client_pool=args.appproxy_client_pool,
        ),
        metric=MetricService(
            metric_repository=repositories.metric.repository,
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
            deployment_repository=repositories.deployment.repository,
            runtime_variant_repository=repositories.runtime_variant.repository,
            scheduler_repository=repositories.scheduler.repository,
            deployment_controller=args.deployment_controller,
            scheduling_controller=args.scheduling_controller,
            route_controller=args.route_controller,
        ),
        model_serving_auto_scaling=AutoScalingService(
            repository=repositories.model_serving.repository,
        ),
        auth=AuthService(
            hook_plugin_ctx=args.hook_plugin_ctx,
            auth_repository=repositories.auth.repository,
            config_provider=args.config_provider,
            valkey_session_client=args.valkey_session_client,
            user_resource_policy_repository=repositories.user_resource_policy.repository,
            user_repository=repositories.user.repository,
            group_repository=repositories.group.repository,
            ssh_key_validator=args.ssh_key_validator,
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
            group_repository=repositories.group.repository,
            rbac_action_registry=RBAC_ACTION_REGISTRY,
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
            repositories.deployment.repository,
            deployment_revision_preset_repository=repositories.deployment_revision_preset.repository,
            runtime_variant_preset_repository=repositories.runtime_variant_preset.repository,
            appproxy_client_pool=args.appproxy_client_pool,
        ),
        idle_checker_assignment=IdleCheckerAssignmentService(repositories.idle_checker.repository),
        scheduling_history=SchedulingHistoryService(repositories.scheduling_history.repository),
        template=TemplateService(
            repository=repositories.template.repository,
        ),
        resource_allocation=ResourceAllocationService(
            resource_allocation_repository=ResourceAllocationRepository(
                db=args.db,
                config_provider=args.config_provider,
            ),
            resource_preset_repository=repositories.resource_preset.repository,
        ),
        stream=StreamService(
            repository=repositories.stream.repository,
            registry=args.agent_registry,
            valkey_live=args.valkey_live,
            etcd=args.etcd,
        ),
        events=EventsService(args.db),
    )


def create_processors(
    args: ProcessorArgs,
    monitors: ActionMonitors,
    validators: ActionValidators,
) -> ProcessorsBundle:
    services = create_services(args.service_args)
    repositories = args.service_args.repositories
    # Legacy BaseAction-era packages consume the flat monitor list; packages migrated
    # to the pure-ABC frameworks pick the per-type monitors from `monitors` instead.
    action_monitors = monitors.legacy
    # One registry shared by every v2-wired package: each package wires through its
    # own group, and the registry's wired_specs() is the catalog of every
    # registered action.
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=args.validators,
            repository=OpsRepository(repositories.v2_ops_provider),
        )
    )
    # Areas covering several entities: every group made here names the area.
    fair_share_groups = registry.concern(ConcernMeta("fair_share"))
    artifact_revisions = registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)).field_group(
        FieldGroupMeta(ARTIFACT_REVISION_FIELD_TYPE),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    resource_slot_groups = registry.concern(ConcernMeta("resource_slot"))
    scheduling_history_groups = registry.concern(ConcernMeta("scheduling_history"))
    resource_allocation_groups = registry.concern(ConcernMeta("resource_allocation"))
    processors = Processors(
        event_hub=args.event_hub,
        event_fetcher=args.event_fetcher,
        events_service=services.events,
        agent=AgentProcessors(
            registry.group(GroupMeta(AGENT_ENTITY_TYPE)),
            services.agent,
            action_monitors,
            validators,
        ),
        app_config=AppConfigProcessors(
            registry.group(GroupMeta(APP_CONFIG_ENTITY_TYPE)),
            registry.group(GroupMeta(APP_CONFIG_DEFINITION_ENTITY_TYPE)),
            registry.group(GroupMeta(APP_CONFIG_ALLOW_LIST_ENTITY_TYPE)),
            registry.group(GroupMeta(APP_CONFIG_FRAGMENT_ENTITY_TYPE)),
            services.app_config,
        ),
        domain=DomainProcessors(
            registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)), services.domain, action_monitors
        ),
        etcd_config=EtcdConfigProcessors(
            registry.group(GroupMeta(ETCD_CONFIG_ENTITY_TYPE)), services.etcd_config
        ),
        export=ExportProcessors(registry.group(GroupMeta(EXPORT_ENTITY_TYPE)), services.export),
        fair_share=FairShareProcessors(
            fair_share_groups.group(GroupMeta(DOMAIN_FAIR_SHARE_ENTITY_TYPE)),
            fair_share_groups.group(GroupMeta(PROJECT_FAIR_SHARE_ENTITY_TYPE)),
            fair_share_groups.group(GroupMeta(USER_FAIR_SHARE_ENTITY_TYPE)),
            services.fair_share,
        ),
        group=GroupProcessors(registry.group(GroupMeta(PROJECT_ENTITY_TYPE)), services.group),
        user=UserProcessors(
            registry.group(GroupMeta(USER_ENTITY_TYPE)),
            services.user,
        ),
        idle_checker=IdleCheckerProcessors(
            registry.group(GroupMeta(SESSION_ENTITY_TYPE)), services.idle_checker, action_monitors
        ),
        image=ImageProcessors(registry.group(GroupMeta(IMAGE_ENTITY_TYPE)), services.image),
        container_registry=ContainerRegistryProcessors(
            registry.group(GroupMeta(CONTAINER_REGISTRY_ENTITY_TYPE)), services.container_registry
        ),
        vfolder=VFolderProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), services.vfolder),
        vfolder_admin=VFolderAdminProcessors(
            registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), services.vfolder_admin
        ),
        vfolder_file=VFolderFileProcessors(
            registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), services.vfolder_file
        ),
        vfolder_invite=VFolderInviteProcessors(
            registry.group(GroupMeta(VFOLDER_INVITATION_ENTITY_TYPE)), services.vfolder_invite
        ),
        vfolder_sharing=VFolderSharingProcessors(
            registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), services.vfolder_sharing
        ),
        session=SessionProcessors(
            registry.group(GroupMeta(SESSION_ENTITY_TYPE)),
            ResourceAllocationProcessors(
                resource_allocation_groups.group(GroupMeta(USER_ENTITY_TYPE)),
                resource_allocation_groups.group(GroupMeta(PROJECT_ENTITY_TYPE)),
                resource_allocation_groups.group(GroupMeta(DOMAIN_ENTITY_TYPE)),
                resource_allocation_groups.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)),
                resource_allocation_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
                resource_allocation_groups.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)),
                services.resource_allocation,
            ),
            services.session,
        ),
        keypair_resource_policy=KeypairResourcePolicyProcessors(
            registry.group(GroupMeta(KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE))
        ),
        manager_admin=ManagerAdminProcessors(
            registry.group(GroupMeta(MANAGER_ADMIN_ENTITY_TYPE)), services.manager_admin
        ),
        user_resource_policy=UserResourcePolicyProcessors(
            registry.group(GroupMeta(USER_RESOURCE_POLICY_ENTITY_TYPE))
        ),
        project_resource_policy=ProjectResourcePolicyProcessors(
            registry.group(GroupMeta(PROJECT_RESOURCE_POLICY_ENTITY_TYPE))
        ),
        prometheus_query_preset=PrometheusQueryPresetProcessors(
            registry.group(GroupMeta(PROMETHEUS_QUERY_PRESET_ENTITY_TYPE)),
            services.prometheus_query_preset,
        ),
        prometheus_query_preset_category=PrometheusQueryPresetCategoryProcessors(
            registry.group(GroupMeta(PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE))
        ),
        resource_preset=ResourcePresetProcessors(
            registry.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)), services.resource_preset
        ),
        resource_slot=ResourceSlotProcessors(
            resource_slot_groups.group(GroupMeta(RESOURCE_SLOT_TYPE_ENTITY_TYPE)),
            resource_slot_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
            resource_slot_groups.group(GroupMeta(AGENT_ENTITY_TYPE)),
            services.resource_slot,
        ),
        retention_policy=RetentionPolicyProcessors(
            registry.group(GroupMeta(RETENTION_POLICY_ENTITY_TYPE))
        ),
        role_preset=RolePresetProcessors(
            registry.group(GroupMeta(ROLE_PRESET_ENTITY_TYPE)), services.role_preset
        ),
        runtime_variant=RuntimeVariantProcessors(
            registry.group(GroupMeta(RUNTIME_VARIANT_ENTITY_TYPE))
        ),
        runtime_variant_preset=RuntimeVariantPresetProcessors(
            registry.group(GroupMeta(RUNTIME_VARIANT_PRESET_ENTITY_TYPE)),
            services.runtime_variant_preset,
        ),
        deployment_revision_preset=DeploymentPresetProcessors(
            registry.group(GroupMeta(DEPLOYMENT_PRESET_ENTITY_TYPE)),
            services.deployment_revision_preset,
        ),
        model_card=ModelCardProcessors(
            registry.group(GroupMeta(MODEL_CARD_ENTITY_TYPE)), services.model_card
        ),
        resource_usage=ResourceUsageProcessors(
            registry.dangling_field_group(
                FieldGroupMeta(DOMAIN_USAGE_BUCKET_FIELD_TYPE), DomainUsageBucketData
            ),
            registry.dangling_field_group(
                FieldGroupMeta(PROJECT_USAGE_BUCKET_FIELD_TYPE), ProjectUsageBucketData
            ),
            registry.dangling_field_group(
                FieldGroupMeta(USER_USAGE_BUCKET_FIELD_TYPE), UserUsageBucketData
            ),
        ),
        resource_group=ResourceGroupProcessors(
            registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), services.resource_group
        ),
        metric=MetricProcessors(services.metric, action_monitors, validators),
        model_serving=ModelServingProcessors(
            registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), services.model_serving
        ),
        model_serving_auto_scaling=ModelServingAutoScalingProcessors(
            registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), services.model_serving_auto_scaling
        ),
        auth=AuthProcessors(services.auth, action_monitors, validators),
        login_client_type=LoginClientTypeProcessors(
            registry.group(GroupMeta(LOGIN_CLIENT_TYPE_ENTITY_TYPE))
        ),
        notification=NotificationProcessors(
            registry.group(GroupMeta(NOTIFICATION_CHANNEL_ENTITY_TYPE)),
            registry.group(GroupMeta(NOTIFICATION_RULE_ENTITY_TYPE)),
            services.notification,
        ),
        object_storage=ObjectStorageProcessors(
            registry.group(GroupMeta(OBJECT_STORAGE_ENTITY_TYPE)),
            artifact_revisions,
            services.object_storage,
        ),
        permission_controller=PermissionControllerProcessors(
            services.permission_controller, action_monitors, validators
        ),
        vfs_storage=VFSStorageProcessors(
            registry.group(GroupMeta(VFS_STORAGE_ENTITY_TYPE)), services.vfs_storage
        ),
        artifact=ArtifactProcessors(
            registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)),
            ArtifactRevisionProcessors(
                registry.group(GroupMeta(ARTIFACT_ENTITY_TYPE)),
                artifact_revisions,
                services.artifact_revision,
            ),
            services.artifact,
        ),
        artifact_registry=ArtifactRegistryProcessors(
            registry.group(GroupMeta(ARTIFACT_REGISTRY_ENTITY_TYPE)), services.artifact_registry
        ),
        deployment=DeploymentProcessors(
            registry.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)), services.deployment
        ),
        storage_namespace=StorageNamespaceProcessors(
            registry.group(GroupMeta(STORAGE_NAMESPACE_ENTITY_TYPE))
        ),
        audit_log=AuditLogProcessors(
            registry.dangling_field_group(FieldGroupMeta(AUDIT_LOG_FIELD_TYPE), AuditLogData)
        ),
        idle_checker_assignment=IdleCheckerAssignmentProcessors(
            services.idle_checker_assignment, action_monitors, validators
        ),
        scheduling_history=SchedulingHistoryProcessors(
            scheduling_history_groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
            scheduling_history_groups.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)),
            scheduling_history_groups.group(GroupMeta(DEPLOYMENT_ENTITY_TYPE)),
            services.scheduling_history,
        ),
        service_catalog=ServiceCatalogProcessors(
            registry.group(GroupMeta(SERVICE_CATALOG_ENTITY_TYPE))
        ),
        template=TemplateProcessors(
            registry.group(GroupMeta(SESSION_TEMPLATE_ENTITY_TYPE)), services.template
        ),
        stream=StreamProcessors(registry.group(GroupMeta(SESSION_ENTITY_TYPE)), services.stream),
    )
    return ProcessorsBundle(processors=processors, registry=registry)

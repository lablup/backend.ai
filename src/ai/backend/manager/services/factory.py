from typing import Any

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.app_config import AppConfigEntityType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionFieldType
from ai.backend.common.data.entity.audit_log import AuditLogFieldType
from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyEntityType
from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.entity_label import EntityLabelFieldType
from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.export import ExportEntityType
from ai.backend.common.data.entity.fair_share import (
    DomainFairShareEntityType,
    ProjectFairShareEntityType,
    UserFairShareEntityType,
)
from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.notification import (
    NotificationChannelEntityType,
    NotificationRuleEntityType,
)
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.prometheus_query_preset import (
    PrometheusQueryPresetEntityType,
)
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.retention_policy import RetentionPolicyEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.data.entity.secret import SecretFieldType
from ai.backend.common.data.entity.service_catalog import ServiceCatalogEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.session_template import SessionTemplateEntityType
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.usage_bucket import (
    DomainUsageBucketFieldType,
    ProjectUsageBucketFieldType,
    UserUsageBucketFieldType,
)
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.entity.vfolder_invitation import VFolderInvitationEntityType
from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType
from ai.backend.manager.actions.action import RBAC_ACTION_REGISTRY
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.clients.prometheus.preset import PromQLTemplateRenderer
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.entity_label.types import EntityLabelData
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
from ai.backend.manager.services.client_ip_masking.processors import ClientIPMaskingProcessors
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
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.manager.services.entity_label.processors import EntityLabelProcessors
from ai.backend.manager.services.entity_share.processors import (
    EntityShareProcessors,
)
from ai.backend.manager.services.entity_share.service import EntityShareService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService
from ai.backend.manager.services.events.service import EventsService
from ai.backend.manager.services.export.processors import ExportProcessors
from ai.backend.manager.services.export.service import ExportService
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
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
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
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
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
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
from ai.backend.manager.services.secret.processors import SecretProcessors
from ai.backend.manager.services.secret.service import SecretService
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
            BulkOwnCheck(repositories.permission_controller.repository, args.config_provider),
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
        project=ProjectService(
            args.storage_manager,
            args.config_provider,
            args.valkey_stat_client,
            repositories.project,
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
            OpsRepository(repositories.v2_ops_provider),
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
        secret=SecretService(repositories.secret.repository),
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
        role_preset=RolePresetService(
            OpsRepository(repositories.v2_ops_provider), repositories.role_preset.repository
        ),
        rbac_relation=RbacRelationService(
            repositories.rbac.relation,
        ),
        rbac_role=RbacRoleService(
            repositories.permission_controller.repository,
            repositories.rbac.roster,
        ),
        rbac_roster=RbacRosterService(
            repositories.rbac.roster,
        ),
        entity_share=EntityShareService(
            repositories.entity_share.repository,
        ),
        runtime_variant_preset=RuntimeVariantPresetService(
            repositories.runtime_variant_preset.repository,
            OpsRepository(repositories.v2_ops_provider),
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
            group_repository=repositories.project.repository,
            ssh_key_validator=args.ssh_key_validator,
            client_ip_masking_repository=repositories.client_ip_masking.repository,
            key_provider_pool=args.key_provider_pool,
        ),
        notification=NotificationService(
            repository=repositories.notification.repository,
            notification_center=args.notification_center,
        ),
        object_storage=ObjectStorageService(
            artifact_repository=repositories.artifact.repository,
            revision_ops=OpsRepository(repositories.v2_ops_provider),
            object_storage_repository=repositories.object_storage.repository,
            storage_namespace_repository=repositories.storage_namespace.repository,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
        ),
        permission_controller=PermissionControllerService(
            repository=repositories.permission_controller.repository,
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
            revision_ops=OpsRepository(repositories.v2_ops_provider),
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
    # Every group is made through the area it belongs to, so every wiring names one.
    app_config_groups = registry.concern(ConcernMeta(Concern.APP_CONFIG))
    artifact_groups = registry.concern(ConcernMeta(Concern.ARTIFACT_REGISTRY))
    container_registry_groups = registry.concern(ConcernMeta(Concern.CONTAINER_REGISTRY))
    deployment_groups = registry.concern(ConcernMeta(Concern.DEPLOYMENT))
    metric_groups = registry.concern(ConcernMeta(Concern.METRIC))
    notification_groups = registry.concern(ConcernMeta(Concern.NOTIFICATION_CENTER))
    organization_groups = registry.concern(ConcernMeta(Concern.ORGANIZATION))
    rbac_groups = registry.concern(ConcernMeta(Concern.RBAC))
    resource_group_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    resource_policy_groups = registry.concern(ConcernMeta(Concern.RESOURCE_POLICY))
    session_groups = registry.concern(ConcernMeta(Concern.SESSION))
    system_groups = registry.concern(ConcernMeta(Concern.SYSTEM))
    vfolder_groups = registry.concern(ConcernMeta(Concern.VFOLDER))
    visibility_groups = registry.concern(ConcernMeta(Concern.VISIBILITY))
    artifact_revisions = artifact_groups.group(GroupMeta(ArtifactEntityType())).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    processors = Processors(
        event_hub=args.event_hub,
        event_fetcher=args.event_fetcher,
        events_service=services.events,
        agent=AgentProcessors(
            resource_group_groups.group(GroupMeta(AgentEntityType())),
            services.agent,
            action_monitors,
        ),
        app_config=AppConfigProcessors(
            app_config_groups.group(GroupMeta(AppConfigEntityType())),
            app_config_groups.group(GroupMeta(AppConfigDefinitionEntityType())),
            app_config_groups.group(GroupMeta(AppConfigAllowListEntityType())),
            app_config_groups.group(GroupMeta(AppConfigFragmentEntityType())),
            services.app_config,
        ),
        domain=DomainProcessors(
            organization_groups.group(GroupMeta(DomainEntityType())),
            services.domain,
            action_monitors,
        ),
        etcd_config=EtcdConfigProcessors(
            system_groups.group(GroupMeta(GlobalEntityType())), services.etcd_config
        ),
        export=ExportProcessors(
            visibility_groups.group(GroupMeta(ExportEntityType())), services.export
        ),
        fair_share=FairShareProcessors(
            resource_group_groups.group(GroupMeta(DomainFairShareEntityType())),
            resource_group_groups.group(GroupMeta(ProjectFairShareEntityType())),
            resource_group_groups.group(GroupMeta(UserFairShareEntityType())),
            services.fair_share,
        ),
        project=ProjectProcessors(
            organization_groups.group(GroupMeta(ProjectEntityType())), services.project
        ),
        user=UserProcessors(
            organization_groups.group(GroupMeta(UserEntityType())),
            services.user,
        ),
        idle_checker=IdleCheckerProcessors(
            session_groups.group(GroupMeta(IdleCheckerEntityType())),
            session_groups.group(GroupMeta(SessionEntityType())),
            services.idle_checker,
        ),
        image=ImageProcessors(
            container_registry_groups.group(GroupMeta(ImageEntityType())), services.image
        ),
        container_registry=ContainerRegistryProcessors(
            container_registry_groups.group(GroupMeta(ContainerRegistryEntityType())),
            services.container_registry,
        ),
        vfolder=VFolderProcessors(
            vfolder_groups.group(GroupMeta(VFolderEntityType())), services.vfolder
        ),
        vfolder_admin=VFolderAdminProcessors(
            vfolder_groups.group(GroupMeta(VFolderEntityType())), services.vfolder_admin
        ),
        vfolder_file=VFolderFileProcessors(
            vfolder_groups.group(GroupMeta(VFolderEntityType())), services.vfolder_file
        ),
        vfolder_invite=VFolderInviteProcessors(
            vfolder_groups.group(GroupMeta(VFolderInvitationEntityType())),
            services.vfolder_invite,
        ),
        vfolder_sharing=VFolderSharingProcessors(
            vfolder_groups.group(GroupMeta(VFolderEntityType())), services.vfolder_sharing
        ),
        session=SessionProcessors(
            session_groups.group(GroupMeta(SessionEntityType())),
            resource_group_groups.group(GroupMeta(ResourceGroupEntityType())),
            ResourceAllocationProcessors(
                resource_group_groups.group(GroupMeta(UserEntityType())),
                resource_group_groups.group(GroupMeta(ProjectEntityType())),
                resource_group_groups.group(GroupMeta(DomainEntityType())),
                resource_group_groups.group(GroupMeta(ResourceGroupEntityType())),
                resource_group_groups.group(GroupMeta(SessionEntityType())),
                resource_group_groups.group(GroupMeta(ResourcePresetEntityType())),
                services.resource_allocation,
            ),
            services.session,
        ),
        keypair_resource_policy=KeypairResourcePolicyProcessors(
            resource_policy_groups.group(GroupMeta(KeyPairResourcePolicyEntityType()))
        ),
        manager_admin=ManagerAdminProcessors(
            system_groups.group(GroupMeta(GlobalEntityType())), services.manager_admin
        ),
        secret=SecretProcessors(
            system_groups.dangling_field_group(FieldGroupMeta(SecretFieldType())),
            services.secret,
        ),
        user_resource_policy=UserResourcePolicyProcessors(
            resource_policy_groups.group(GroupMeta(UserResourcePolicyEntityType()))
        ),
        project_resource_policy=ProjectResourcePolicyProcessors(
            resource_policy_groups.group(GroupMeta(ProjectResourcePolicyEntityType()))
        ),
        prometheus_query_preset=PrometheusQueryPresetProcessors(
            metric_groups.group(GroupMeta(PrometheusQueryPresetEntityType())),
            services.prometheus_query_preset,
        ),
        prometheus_query_preset_category=PrometheusQueryPresetCategoryProcessors(
            metric_groups.group(GroupMeta(PrometheusQueryPresetCategoryEntityType()))
        ),
        resource_preset=ResourcePresetProcessors(
            resource_group_groups.group(GroupMeta(ResourcePresetEntityType())),
            services.resource_preset,
        ),
        resource_slot=ResourceSlotProcessors(
            system_groups.group(GroupMeta(ResourceSlotTypeEntityType())),
            resource_group_groups.group(GroupMeta(SessionEntityType())),
            resource_group_groups.group(GroupMeta(AgentEntityType())),
            services.resource_slot,
        ),
        retention_policy=RetentionPolicyProcessors(
            system_groups.group(GroupMeta(RetentionPolicyEntityType()))
        ),
        role_preset=RolePresetProcessors(
            rbac_groups.group(GroupMeta(RolePresetEntityType())), services.role_preset
        ),
        runtime_variant=RuntimeVariantProcessors(
            system_groups.group(GroupMeta(RuntimeVariantEntityType()))
        ),
        client_ip_masking=ClientIPMaskingProcessors(
            system_groups.group(GroupMeta(ClientIPMaskingPolicyEntityType()))
        ),
        rbac=RbacProcessors(
            rbac_groups.relation_group(),
            rbac_groups.group(GroupMeta(UserEntityType())),
            services.rbac_relation,
            services.rbac_roster,
            services.rbac_role,
            action_monitors,
        ),
        entity_share=EntityShareProcessors(
            rbac_groups.group(GroupMeta(EntityShareEntityType())),
            services.entity_share,
        ),
        runtime_variant_preset=RuntimeVariantPresetProcessors(
            system_groups.group(GroupMeta(RuntimeVariantPresetEntityType())),
            services.runtime_variant_preset,
        ),
        deployment_revision_preset=DeploymentPresetProcessors(
            deployment_groups.group(GroupMeta(DeploymentPresetEntityType())),
            services.deployment_revision_preset,
        ),
        model_card=ModelCardProcessors(
            deployment_groups.group(GroupMeta(ModelCardEntityType())), services.model_card
        ),
        resource_usage=ResourceUsageProcessors(
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(DomainUsageBucketFieldType()), DomainUsageBucketData
            ),
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(ProjectUsageBucketFieldType()), ProjectUsageBucketData
            ),
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(UserUsageBucketFieldType()), UserUsageBucketData
            ),
        ),
        resource_group=ResourceGroupProcessors(
            resource_group_groups.group(GroupMeta(ResourceGroupEntityType())),
            services.resource_group,
        ),
        metric=MetricProcessors(
            metric_groups.group(GroupMeta(PrometheusQueryPresetEntityType())),
            metric_groups.group(GroupMeta(UserEntityType())),
            session_groups.group(GroupMeta(SessionEntityType())),
            services.metric,
        ),
        model_serving=ModelServingProcessors(
            deployment_groups.group(GroupMeta(DeploymentEntityType())), services.model_serving
        ),
        model_serving_auto_scaling=ModelServingAutoScalingProcessors(
            deployment_groups.group(GroupMeta(DeploymentEntityType())),
            services.model_serving_auto_scaling,
        ),
        auth=AuthProcessors(
            organization_groups.group(GroupMeta(GlobalEntityType())),
            organization_groups.group(GroupMeta(UserEntityType())),
            services.auth,
        ),
        login_client_type=LoginClientTypeProcessors(
            system_groups.group(GroupMeta(LoginClientTypeEntityType()))
        ),
        notification=NotificationProcessors(
            notification_groups.group(GroupMeta(NotificationChannelEntityType())),
            notification_groups.group(GroupMeta(NotificationRuleEntityType())),
            services.notification,
        ),
        object_storage=ObjectStorageProcessors(
            artifact_groups.group(GroupMeta(ObjectStorageEntityType())),
            artifact_revisions,
            services.object_storage,
        ),
        permission_controller=PermissionControllerProcessors(
            rbac_groups.group(GroupMeta(RoleEntityType())),
            services.permission_controller,
            action_monitors,
            validators,
        ),
        vfs_storage=VFSStorageProcessors(
            artifact_groups.group(GroupMeta(VFSStorageEntityType())), services.vfs_storage
        ),
        artifact=ArtifactProcessors(
            artifact_groups.group(GroupMeta(ArtifactEntityType())),
            artifact_revisions,
            ArtifactRevisionProcessors(
                artifact_groups.group(GroupMeta(ArtifactEntityType())),
                artifact_revisions,
                services.artifact_revision,
            ),
            services.artifact,
        ),
        artifact_registry=ArtifactRegistryProcessors(
            artifact_groups.group(GroupMeta(ArtifactRegistryEntityType())),
            services.artifact_registry,
        ),
        deployment=DeploymentProcessors(
            deployment_groups.group(GroupMeta(DeploymentEntityType())), services.deployment
        ),
        storage_namespace=StorageNamespaceProcessors(
            artifact_groups.group(GroupMeta(StorageNamespaceEntityType()))
        ),
        audit_log=AuditLogProcessors(
            visibility_groups.dangling_field_group(
                FieldGroupMeta(AuditLogFieldType()), AuditLogData
            )
        ),
        entity_label=EntityLabelProcessors(
            registry.dangling_lookup_field_group(
                FieldGroupMeta(EntityLabelFieldType()),
                EntityLabelData,
                LookupEntityLabelOwnerAction,
                LookupBulkEntityLabelOwnerAction,
            )
        ),
        idle_checker_assignment=IdleCheckerAssignmentProcessors(
            session_groups.group(GroupMeta(IdleCheckerEntityType())),
            services.idle_checker_assignment,
        ),
        scheduling_history=SchedulingHistoryProcessors(
            session_groups.group(GroupMeta(SessionEntityType())),
            deployment_groups.group(GroupMeta(DeploymentEntityType())),
            deployment_groups.group(GroupMeta(DeploymentEntityType())),
            services.scheduling_history,
        ),
        service_catalog=ServiceCatalogProcessors(
            system_groups.group(GroupMeta(ServiceCatalogEntityType()))
        ),
        template=TemplateProcessors(
            session_groups.group(GroupMeta(SessionTemplateEntityType())), services.template
        ),
        stream=StreamProcessors(
            session_groups.group(GroupMeta(SessionEntityType())), services.stream
        ),
    )
    return ProcessorsBundle(processors=processors, registry=registry)

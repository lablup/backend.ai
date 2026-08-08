from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.actions.v2.validators import ActionValidators

# fmt: off
if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
        ValkeyArtifactDownloadTrackingClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_live.client import (
        ValkeyLiveClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_session.client import (
        ValkeySessionClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_stat.client import (
        ValkeyStatClient,
    )
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.events.dispatcher import (
        EventDispatcher,
        EventProducer,
    )
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.common.plugin.hook import HookPluginContext
    from ai.backend.common.plugin.monitor import ErrorPluginContext
    from ai.backend.manager.agent_cache import AgentRPCCache
    from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
    from ai.backend.manager.clients.prometheus.client import PrometheusClient
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.idle import IdleCheckerHost
    from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.notification import NotificationCenter
    from ai.backend.manager.registry import AgentRegistry
    from ai.backend.manager.repositories.repositories import Repositories
    from ai.backend.manager.service.container_registry.harbor import (
        AbstractPerProjectContainerRegistryQuotaService,
    )
    from ai.backend.manager.services.agent.processors import AgentProcessors
    from ai.backend.manager.services.agent.service import AgentService
    from ai.backend.manager.services.app_config.processors import (
        AppConfigProcessors,
    )
    from ai.backend.manager.services.app_config.service import (
        AppConfigService,
    )
    from ai.backend.manager.services.app_config_allow_list.processors import (
        AppConfigAllowListProcessors,
    )
    from ai.backend.manager.services.app_config_definition.processors import (
        AppConfigDefinitionProcessors,
    )
    from ai.backend.manager.services.app_config_definition.service import (
        AppConfigDefinitionService,
    )
    from ai.backend.manager.services.app_config_fragment.processors import (
        AppConfigFragmentProcessors,
    )
    from ai.backend.manager.services.app_config_fragment.service import (
        AppConfigFragmentService,
    )
    from ai.backend.manager.services.artifact.processors import (
        ArtifactProcessors,
    )
    from ai.backend.manager.services.artifact.service import ArtifactService
    from ai.backend.manager.services.artifact_registry.processors import (
        ArtifactRegistryProcessors,
    )
    from ai.backend.manager.services.artifact_registry.service import (
        ArtifactRegistryService,
    )
    from ai.backend.manager.services.artifact_revision.processors import (
        ArtifactRevisionProcessors,
    )
    from ai.backend.manager.services.artifact_revision.service import (
        ArtifactRevisionService,
    )
    from ai.backend.manager.services.audit_log.processors import (
        AuditLogProcessors,
    )
    from ai.backend.manager.services.audit_log.service import AuditLogService
    from ai.backend.manager.services.auth.processors import AuthProcessors
    from ai.backend.manager.services.auth.service import AuthService
    from ai.backend.manager.services.container_registry.processors import (
        ContainerRegistryProcessors,
    )
    from ai.backend.manager.services.container_registry.service import (
        ContainerRegistryService,
    )
    from ai.backend.manager.services.deployment.processors import (
        DeploymentProcessors,
    )
    from ai.backend.manager.services.deployment.service import (
        DeploymentService,
    )
    from ai.backend.manager.services.deployment_revision_preset.processors import (
        DeploymentRevisionPresetProcessors,
    )
    from ai.backend.manager.services.deployment_revision_preset.service import (
        DeploymentRevisionPresetService,
    )
    from ai.backend.manager.services.domain.processors import (
        DomainProcessors,
    )
    from ai.backend.manager.services.domain.service import DomainService
    from ai.backend.manager.services.dotfile.processors import (
        DotfileProcessors,
    )
    from ai.backend.manager.services.dotfile.service import DotfileService
    from ai.backend.manager.services.error_log.processors import (
        ErrorLogProcessors,
    )
    from ai.backend.manager.services.error_log.service import ErrorLogService
    from ai.backend.manager.services.etcd_config.processors import (
        EtcdConfigProcessors,
    )
    from ai.backend.manager.services.etcd_config.service import (
        EtcdConfigService,
    )
    from ai.backend.manager.services.events.processors import (
        EventsProcessors,
    )
    from ai.backend.manager.services.events.service import EventsService
    from ai.backend.manager.services.export.processors import (
        ExportProcessors,
    )
    from ai.backend.manager.services.export.service import ExportService
    from ai.backend.manager.services.fair_share.processors import (
        FairShareProcessors,
    )
    from ai.backend.manager.services.fair_share.service import (
        FairShareService,
    )
    from ai.backend.manager.services.group.processors import GroupProcessors
    from ai.backend.manager.services.group.service import GroupService
    from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
    from ai.backend.manager.services.idle_checker.service import IdleCheckerService
    from ai.backend.manager.services.idle_checker_assignment.processors import (
        IdleCheckerAssignmentProcessors,
    )
    from ai.backend.manager.services.idle_checker_assignment.service import (
        IdleCheckerAssignmentService,
    )
    from ai.backend.manager.services.image.processors import ImageProcessors
    from ai.backend.manager.services.image.service import ImageService
    from ai.backend.manager.services.keypair_resource_policy.processors import (
        KeypairResourcePolicyProcessors,
    )
    from ai.backend.manager.services.keypair_resource_policy.service import (
        KeypairResourcePolicyService,
    )
    from ai.backend.manager.services.login_client_type.admin_service import (
        LoginClientTypeAdminService,
    )
    from ai.backend.manager.services.login_client_type.processors import (
        LoginClientTypeAdminProcessors,
        LoginClientTypeProcessors,
    )
    from ai.backend.manager.services.login_client_type.service import (
        LoginClientTypeService,
    )
    from ai.backend.manager.services.manager_admin.processors import (
        ManagerAdminProcessors,
    )
    from ai.backend.manager.services.manager_admin.service import (
        ManagerAdminService,
    )
    from ai.backend.manager.services.metric.processors import (
        MetricProcessors,
    )
    from ai.backend.manager.services.metric.service import (
        MetricService,
    )
    from ai.backend.manager.services.model_card.processors import (
        ModelCardProcessors,
    )
    from ai.backend.manager.services.model_card.service import (
        ModelCardService,
    )
    from ai.backend.manager.services.model_serving.processors.auto_scaling import (
        ModelServingAutoScalingProcessors,
    )
    from ai.backend.manager.services.model_serving.processors.model_serving import (
        ModelServingProcessors,
    )
    from ai.backend.manager.services.model_serving.services.auto_scaling import (
        AutoScalingService,
    )
    from ai.backend.manager.services.model_serving.services.model_serving import (
        ModelServingService,
    )
    from ai.backend.manager.services.notification.processors import (
        NotificationProcessors,
    )
    from ai.backend.manager.services.notification.service import (
        NotificationService,
    )
    from ai.backend.manager.services.object_storage.processors import (
        ObjectStorageProcessors,
    )
    from ai.backend.manager.services.object_storage.service import (
        ObjectStorageService,
    )
    from ai.backend.manager.services.permission_contoller.processors import (
        PermissionControllerProcessors,
    )
    from ai.backend.manager.services.permission_contoller.service import (
        PermissionControllerService,
    )
    from ai.backend.manager.services.project_resource_policy.processors import (
        ProjectResourcePolicyProcessors,
    )
    from ai.backend.manager.services.project_resource_policy.service import (
        ProjectResourcePolicyService,
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
    from ai.backend.manager.services.prometheus_query_preset_category.service import (
        PrometheusQueryPresetCategoryService,
    )
    from ai.backend.manager.services.resource_allocation.processors import (
        ResourceAllocationProcessors,
    )
    from ai.backend.manager.services.resource_allocation.service import (
        ResourceAllocationService,
    )
    from ai.backend.manager.services.resource_preset.processors import (
        ResourcePresetProcessors,
    )
    from ai.backend.manager.services.resource_preset.service import (
        ResourcePresetService,
    )
    from ai.backend.manager.services.resource_slot.processors import (
        ResourceSlotProcessors,
    )
    from ai.backend.manager.services.resource_slot.service import (
        ResourceSlotService,
    )
    from ai.backend.manager.services.resource_usage.processors import (
        ResourceUsageProcessors,
    )
    from ai.backend.manager.services.resource_usage.service import (
        ResourceUsageService,
    )
    from ai.backend.manager.services.retention_policy.processors import (
        RetentionPolicyProcessors,
    )
    from ai.backend.manager.services.retention_policy.service import (
        RetentionPolicyService,
    )
    from ai.backend.manager.services.role_preset.processors import (
        RolePresetProcessors,
    )
    from ai.backend.manager.services.role_preset.service import (
        RolePresetService,
    )
    from ai.backend.manager.services.runtime_variant.processors import (
        RuntimeVariantProcessors,
    )
    from ai.backend.manager.services.runtime_variant.service import (
        RuntimeVariantService,
    )
    from ai.backend.manager.services.runtime_variant_preset.processors import (
        RuntimeVariantPresetProcessors,
    )
    from ai.backend.manager.services.runtime_variant_preset.service import (
        RuntimeVariantPresetService,
    )
    from ai.backend.manager.services.scaling_group.processors import (
        ScalingGroupProcessors,
    )
    from ai.backend.manager.services.scaling_group.service import (
        ScalingGroupService,
    )
    from ai.backend.manager.services.scheduling_history.processors import (
        SchedulingHistoryProcessors,
    )
    from ai.backend.manager.services.scheduling_history.service import (
        SchedulingHistoryService,
    )
    from ai.backend.manager.services.service_catalog.processors import (
        ServiceCatalogProcessors,
    )
    from ai.backend.manager.services.service_catalog.service import (
        ServiceCatalogService,
    )
    from ai.backend.manager.services.session.processors import (
        SessionProcessors,
    )
    from ai.backend.manager.services.session.service import SessionService
    from ai.backend.manager.services.storage_namespace.processors import (
        StorageNamespaceProcessors,
    )
    from ai.backend.manager.services.storage_namespace.service import (
        StorageNamespaceService,
    )
    from ai.backend.manager.services.stream.processors import (
        StreamProcessors,
    )
    from ai.backend.manager.services.stream.service import StreamService
    from ai.backend.manager.services.template.processors import (
        TemplateProcessors,
    )
    from ai.backend.manager.services.template.service import TemplateService
    from ai.backend.manager.services.user.processors import UserProcessors
    from ai.backend.manager.services.user.service import UserService
    from ai.backend.manager.services.user_resource_policy.processors import (
        UserResourcePolicyProcessors,
    )
    from ai.backend.manager.services.user_resource_policy.service import (
        UserResourcePolicyService,
    )
    from ai.backend.manager.services.vfolder.processors import (
        VFolderFileProcessors,
        VFolderInviteProcessors,
        VFolderProcessors,
        VFolderSharingProcessors,
    )
    from ai.backend.manager.services.vfolder.processors.vfolder_admin import (
        VFolderAdminProcessors,
    )
    from ai.backend.manager.services.vfolder.services.file import (
        VFolderFileService,
    )
    from ai.backend.manager.services.vfolder.services.invite import (
        VFolderInviteService,
    )
    from ai.backend.manager.services.vfolder.services.sharing import (
        VFolderSharingService,
    )
    from ai.backend.manager.services.vfolder.services.vfolder import (
        VFolderService,
    )
    from ai.backend.manager.services.vfolder.services.vfolder_admin import (
        VFolderAdminService,
    )
    from ai.backend.manager.services.vfs_storage.processors import (
        VFSStorageProcessors,
    )
    from ai.backend.manager.services.vfs_storage.service import (
        VFSStorageService,
    )
    from ai.backend.manager.sokovan.deployment import DeploymentController
    from ai.backend.manager.sokovan.deployment.route.route_controller import (
        RouteController,
    )
    from ai.backend.manager.sokovan.scheduling_controller import (
        SchedulingController,
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
    valkey_session_client: ValkeySessionClient
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
    route_controller: RouteController
    event_producer: EventProducer
    agent_cache: AgentRPCCache
    notification_center: NotificationCenter
    appproxy_client_pool: AppProxyClientPool
    prometheus_client: PrometheusClient
    ssh_key_validator: SSHKeyValidator
    registry_quota_service: AbstractPerProjectContainerRegistryQuotaService | None = None


@dataclass
class Services:
    agent: AgentService
    app_config: AppConfigService
    app_config_definition: AppConfigDefinitionService
    app_config_fragment: AppConfigFragmentService
    domain: DomainService
    dotfile: DotfileService
    error_log: ErrorLogService
    etcd_config: EtcdConfigService
    export: ExportService
    fair_share: FairShareService
    group: GroupService
    user: UserService
    idle_checker: IdleCheckerService
    image: ImageService
    container_registry: ContainerRegistryService
    vfolder: VFolderService
    vfolder_admin: VFolderAdminService
    vfolder_file: VFolderFileService
    vfolder_invite: VFolderInviteService
    vfolder_sharing: VFolderSharingService
    session: SessionService
    keypair_resource_policy: KeypairResourcePolicyService
    manager_admin: ManagerAdminService
    user_resource_policy: UserResourcePolicyService
    project_resource_policy: ProjectResourcePolicyService
    prometheus_query_preset: PrometheusQueryPresetService
    prometheus_query_preset_category: PrometheusQueryPresetCategoryService
    resource_preset: ResourcePresetService
    resource_slot: ResourceSlotService
    retention_policy: RetentionPolicyService
    role_preset: RolePresetService
    runtime_variant: RuntimeVariantService
    runtime_variant_preset: RuntimeVariantPresetService
    deployment_revision_preset: DeploymentRevisionPresetService
    model_card: ModelCardService
    resource_usage: ResourceUsageService
    scaling_group: ScalingGroupService
    metric: MetricService
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
    idle_checker_assignment: IdleCheckerAssignmentService
    scheduling_history: SchedulingHistoryService
    service_catalog: ServiceCatalogService
    template: TemplateService
    resource_allocation: ResourceAllocationService
    stream: StreamService
    events: EventsService
    login_client_type: LoginClientTypeService
    login_client_type_admin: LoginClientTypeAdminService


@dataclass
class ProcessorArgs:
    service_args: ServiceArgs
    event_hub: EventHub
    event_fetcher: EventFetcher
    validators: ActionValidators


@dataclass
class Processors:
    agent: AgentProcessors
    app_config: AppConfigProcessors
    app_config_allow_list: AppConfigAllowListProcessors
    app_config_definition: AppConfigDefinitionProcessors
    app_config_fragment: AppConfigFragmentProcessors
    domain: DomainProcessors
    dotfile: DotfileProcessors
    error_log: ErrorLogProcessors
    etcd_config: EtcdConfigProcessors
    export: ExportProcessors
    fair_share: FairShareProcessors
    group: GroupProcessors
    user: UserProcessors
    idle_checker: IdleCheckerProcessors
    image: ImageProcessors
    vfolder: VFolderProcessors
    vfolder_admin: VFolderAdminProcessors
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
    prometheus_query_preset_category: PrometheusQueryPresetCategoryProcessors
    resource_preset: ResourcePresetProcessors
    resource_slot: ResourceSlotProcessors
    retention_policy: RetentionPolicyProcessors
    role_preset: RolePresetProcessors
    runtime_variant: RuntimeVariantProcessors
    runtime_variant_preset: RuntimeVariantPresetProcessors
    deployment_revision_preset: DeploymentRevisionPresetProcessors
    model_card: ModelCardProcessors
    resource_usage: ResourceUsageProcessors
    scaling_group: ScalingGroupProcessors
    metric: MetricProcessors
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
    idle_checker_assignment: IdleCheckerAssignmentProcessors
    scheduling_history: SchedulingHistoryProcessors
    service_catalog: ServiceCatalogProcessors
    template: TemplateProcessors
    resource_allocation: ResourceAllocationProcessors
    stream: StreamProcessors
    events: EventsProcessors
    login_client_type: LoginClientTypeProcessors
    login_client_type_admin: LoginClientTypeAdminProcessors

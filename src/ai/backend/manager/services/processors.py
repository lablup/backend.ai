from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
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
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.artifact.processors import ArtifactProcessors
from ai.backend.manager.services.artifact.service import ArtifactService
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService
from ai.backend.manager.services.artifact_revision.processors import ArtifactRevisionProcessors
from ai.backend.manager.services.artifact_revision.service import ArtifactRevisionService
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.keypair_resource_policy.service import KeypairResourcePolicyService
from ai.backend.manager.services.metric.processors.utilization_metric import (
    UtilizationMetricProcessors,
)
from ai.backend.manager.services.metric.root_service import UtilizationMetricService
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
    ModelServingServiceProtocol,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.services.model_serving.services.model_serving import (
    ModelServingService,
)
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService
from ai.backend.manager.services.vfolder.processors import (
    VFolderFileProcessors,
    VFolderInviteProcessors,
    VFolderProcessors,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.sokovan.deployment import DeploymentController
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
    event_producer: EventProducer
    agent_cache: AgentRPCCache


@dataclass
class Services:
    agent: AgentService
    domain: DomainService
    group: GroupService
    user: UserService
    image: ImageService
    container_registry: ContainerRegistryService
    vfolder: VFolderService
    vfolder_file: VFolderFileService
    vfolder_invite: VFolderInviteService
    session: SessionService
    keypair_resource_policy: KeypairResourcePolicyService
    user_resource_policy: UserResourcePolicyService
    project_resource_policy: ProjectResourcePolicyService
    resource_preset: ResourcePresetService
    utilization_metric: UtilizationMetricService
    model_serving: ModelServingServiceProtocol
    model_serving_auto_scaling: AutoScalingService
    auth: AuthService
    object_storage: ObjectStorageService
    artifact: ArtifactService
    artifact_revision: ArtifactRevisionService
    artifact_registry: ArtifactRegistryService
    deployment: DeploymentService
    storage_namespace: StorageNamespaceService

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
        domain_service = DomainService(
            repositories.domain.repository, repositories.domain.admin_repository
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
            repositories.user.admin_repository,
        )
        image_service = ImageService(
            args.agent_registry, repositories.image.repository, repositories.image.admin_repository
        )
        container_registry_service = ContainerRegistryService(
            args.db,
            repositories.container_registry.repository,
            repositories.container_registry.admin_repository,
        )
        vfolder_service = VFolderService(
            args.config_provider,
            args.storage_manager,
            args.background_task_manager,
            repositories.vfolder.repository,
            repositories.user.repository,
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
        session_service = SessionService(
            SessionServiceArgs(
                agent_registry=args.agent_registry,
                event_fetcher=args.event_fetcher,
                background_task_manager=args.background_task_manager,
                event_hub=args.event_hub,
                error_monitor=args.error_monitor,
                idle_checker_host=args.idle_checker_host,
                session_repository=repositories.session.repository,
                admin_session_repository=repositories.session.admin_repository,
                scheduling_controller=args.scheduling_controller,
            )
        )
        keypair_resource_policy_service = KeypairResourcePolicyService(
            repositories.keypair_resource_policy.repository
        )
        user_resource_policy_service = UserResourcePolicyService(
            repositories.user_resource_policy.repository
        )
        project_resource_policy_service = ProjectResourcePolicyService(
            repositories.project_resource_policy.repository
        )
        resource_preset_service = ResourcePresetService(
            repositories.resource_preset.repository,
        )
        utilization_metric_service = UtilizationMetricService(
            args.config_provider, repositories.metric.repository
        )

        # Use deployment-based model serving if deployment_controller is available
        model_serving_service = ModelServingService(
            agent_registry=args.agent_registry,
            background_task_manager=args.background_task_manager,
            event_dispatcher=args.event_dispatcher,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
            valkey_live=args.valkey_live,
            repository=repositories.model_serving.repository,
            admin_repository=repositories.model_serving.admin_repository,
            deployment_controller=args.deployment_controller,
        )

        model_serving_auto_scaling = AutoScalingService(
            repository=repositories.model_serving.repository,
            admin_repository=repositories.model_serving.admin_repository,
        )
        auth = AuthService(
            hook_plugin_ctx=args.hook_plugin_ctx,
            auth_repository=repositories.auth.repository,
            config_provider=args.config_provider,
        )
        object_storage_service = ObjectStorageService(
            artifact_repository=repositories.artifact.repository,
            object_storage_repository=repositories.object_storage.repository,
            storage_manager=args.storage_manager,
            config_provider=args.config_provider,
        )
        artifact_service = ArtifactService(
            artifact_repository=repositories.artifact.repository,
            artifact_registry_repository=repositories.artifact_registry.repository,
            storage_manager=args.storage_manager,
            object_storage_repository=repositories.object_storage.repository,
            huggingface_registry_repository=repositories.huggingface_registry.repository,
            config_provider=args.config_provider,
            reservoir_registry_repository=repositories.reservoir_registry.repository,
        )
        artifact_revision_service = ArtifactRevisionService(
            artifact_repository=repositories.artifact.repository,
            storage_manager=args.storage_manager,
            object_storage_repository=repositories.object_storage.repository,
            huggingface_registry_repository=repositories.huggingface_registry.repository,
            reservoir_registry_repository=repositories.reservoir_registry.repository,
            config_provider=args.config_provider,
        )
        artifact_registry_service = ArtifactRegistryService(
            repositories.huggingface_registry.repository,
            repositories.reservoir_registry.repository,
            repositories.artifact_registry.repository,
        )
        deployment_service = DeploymentService(args.deployment_controller)
        storage_namespace_service = StorageNamespaceService(
            repositories.storage_namespace.repository
        )

        return cls(
            agent=agent_service,
            domain=domain_service,
            group=group_service,
            user=user_service,
            image=image_service,
            container_registry=container_registry_service,
            vfolder=vfolder_service,
            vfolder_file=vfolder_file_service,
            vfolder_invite=vfolder_invite_service,
            session=session_service,
            keypair_resource_policy=keypair_resource_policy_service,
            user_resource_policy=user_resource_policy_service,
            project_resource_policy=project_resource_policy_service,
            resource_preset=resource_preset_service,
            utilization_metric=utilization_metric_service,
            model_serving=model_serving_service,
            model_serving_auto_scaling=model_serving_auto_scaling,
            auth=auth,
            object_storage=object_storage_service,
            artifact=artifact_service,
            artifact_revision=artifact_revision_service,
            artifact_registry=artifact_registry_service,
            deployment=deployment_service,
            storage_namespace=storage_namespace_service,
        )


@dataclass
class ProcessorArgs:
    service_args: ServiceArgs


@dataclass
class Processors(AbstractProcessorPackage):
    agent: AgentProcessors
    domain: DomainProcessors
    group: GroupProcessors
    user: UserProcessors
    image: ImageProcessors
    vfolder: VFolderProcessors
    vfolder_invite: VFolderInviteProcessors
    vfolder_file: VFolderFileProcessors
    session: SessionProcessors
    container_registry: ContainerRegistryProcessors
    keypair_resource_policy: KeypairResourcePolicyProcessors
    user_resource_policy: UserResourcePolicyProcessors
    project_resource_policy: ProjectResourcePolicyProcessors
    resource_preset: ResourcePresetProcessors
    utilization_metric: UtilizationMetricProcessors
    model_serving: ModelServingProcessors
    model_serving_auto_scaling: ModelServingAutoScalingProcessors
    auth: AuthProcessors
    object_storage: ObjectStorageProcessors
    artifact: ArtifactProcessors
    artifact_registry: ArtifactRegistryProcessors
    artifact_revision: ArtifactRevisionProcessors
    deployment: Optional[DeploymentProcessors]
    storage_namespace: StorageNamespaceProcessors

    @classmethod
    def create(cls, args: ProcessorArgs, action_monitors: list[ActionMonitor]) -> Self:
        services = Services.create(args.service_args)
        agent_processors = AgentProcessors(services.agent, action_monitors)
        domain_processors = DomainProcessors(services.domain, action_monitors)
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
        session_processors = SessionProcessors(services.session, action_monitors)
        keypair_resource_policy_processors = KeypairResourcePolicyProcessors(
            services.keypair_resource_policy, action_monitors
        )
        user_resource_policy_processors = UserResourcePolicyProcessors(
            services.user_resource_policy, action_monitors
        )
        project_resource_policy_processors = ProjectResourcePolicyProcessors(
            services.project_resource_policy, action_monitors
        )
        resource_preset_processors = ResourcePresetProcessors(
            services.resource_preset, action_monitors
        )
        model_serving_processors = ModelServingProcessors(services.model_serving, action_monitors)
        model_serving_auto_scaling_processors = ModelServingAutoScalingProcessors(
            services.model_serving_auto_scaling, action_monitors
        )
        utilization_metric_processors = UtilizationMetricProcessors(
            services.utilization_metric, action_monitors
        )
        auth = AuthProcessors(services.auth, action_monitors)
        object_storage_processors = ObjectStorageProcessors(
            services.object_storage, action_monitors
        )
        artifact_processors = ArtifactProcessors(services.artifact, action_monitors)
        artifact_registry_processors = ArtifactRegistryProcessors(
            services.artifact_registry, action_monitors
        )
        artifact_revision_processors = ArtifactRevisionProcessors(
            services.artifact_revision, action_monitors
        )

        # Initialize deployment processors if service is available
        deployment_processors = None
        if services.deployment is not None:
            deployment_processors = DeploymentProcessors(services.deployment, action_monitors)

        storage_namespace_processors = StorageNamespaceProcessors(
            services.storage_namespace, action_monitors
        )

        return cls(
            agent=agent_processors,
            domain=domain_processors,
            group=group_processors,
            user=user_processors,
            image=image_processors,
            container_registry=container_registry_processors,
            vfolder=vfolder_processors,
            vfolder_file=vfolder_file_processors,
            vfolder_invite=vfolder_invite_processors,
            session=session_processors,
            keypair_resource_policy=keypair_resource_policy_processors,
            user_resource_policy=user_resource_policy_processors,
            project_resource_policy=project_resource_policy_processors,
            resource_preset=resource_preset_processors,
            utilization_metric=utilization_metric_processors,
            model_serving=model_serving_processors,
            model_serving_auto_scaling=model_serving_auto_scaling_processors,
            auth=auth,
            object_storage=object_storage_processors,
            artifact=artifact_processors,
            artifact_registry=artifact_registry_processors,
            artifact_revision=artifact_revision_processors,
            deployment=deployment_processors,
            storage_namespace=storage_namespace_processors,
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            *self.agent.supported_actions(),
            *self.domain.supported_actions(),
            *self.group.supported_actions(),
            *self.user.supported_actions(),
            *self.image.supported_actions(),
            *self.container_registry.supported_actions(),
            *self.vfolder.supported_actions(),
            *self.vfolder_file.supported_actions(),
            *self.vfolder_invite.supported_actions(),
            *self.session.supported_actions(),
            *self.keypair_resource_policy.supported_actions(),
            *self.user_resource_policy.supported_actions(),
            *self.project_resource_policy.supported_actions(),
            *self.resource_preset.supported_actions(),
            *self.utilization_metric.supported_actions(),
            *self.model_serving.supported_actions(),
            *self.model_serving_auto_scaling.supported_actions(),
            *self.auth.supported_actions(),
            *self.object_storage.supported_actions(),
            *self.artifact_registry.supported_actions(),
            *self.artifact_revision.supported_actions(),
            *self.artifact.supported_actions(),
            *(self.deployment.supported_actions() if self.deployment else []),
            *self.storage_namespace.supported_actions(),
        ]

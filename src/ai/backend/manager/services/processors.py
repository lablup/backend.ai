from dataclasses import dataclass
from typing import Self

from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
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
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
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


@dataclass
class ServiceArgs:
    db: ExtendedAsyncSAEngine
    shared_config: SharedConfig
    storage_manager: StorageSessionManager
    redis_stat: RedisConnectionInfo
    background_task_manager: BackgroundTaskManager
    agent_registry: AgentRegistry
    error_monitor: ErrorPluginContext
    idle_checker_host: IdleCheckerHost


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

    @classmethod
    def create(cls, args: ServiceArgs) -> Self:
        agent_service = AgentService(
            args.db,
            args.agent_registry,
            args.shared_config,
        )
        domain_service = DomainService(args.db)
        group_service = GroupService(
            args.db, args.storage_manager, args.shared_config, args.redis_stat
        )
        user_service = UserService(args.db, args.storage_manager, args.redis_stat)
        image_service = ImageService(args.db, args.agent_registry)
        container_registry_service = ContainerRegistryService(args.db)
        vfolder_service = VFolderService(
            args.db, args.shared_config, args.storage_manager, args.background_task_manager
        )
        vfolder_file_service = VFolderFileService(args.db, args.shared_config, args.storage_manager)
        vfolder_invite_service = VFolderInviteService(args.db, args.shared_config)
        session_service = SessionService(
            SessionServiceArgs(
                db=args.db,
                agent_registry=args.agent_registry,
                background_task_manager=args.background_task_manager,
                error_monitor=args.error_monitor,
                idle_checker_host=args.idle_checker_host,
            )
        )
        keypair_resource_policy_service = KeypairResourcePolicyService(args.db)
        user_resource_policy_service = UserResourcePolicyService(args.db)
        project_resource_policy_service = ProjectResourcePolicyService(args.db)
        resource_preset_service = ResourcePresetService(
            args.db, args.agent_registry, args.shared_config
        )
        utilization_metric_service = UtilizationMetricService(args.shared_config)

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
        )


@dataclass
class ProcessorArgs:
    service_args: ServiceArgs


@dataclass
class Processors:
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
        utilization_metric_processors = UtilizationMetricProcessors(
            services.utilization_metric, action_monitors
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
        )

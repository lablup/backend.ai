from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repositories import AgentRepositories
from ai.backend.manager.repositories.app_config.repositories import AppConfigRepositories
from ai.backend.manager.repositories.artifact.repositories import ArtifactRepositories
from ai.backend.manager.repositories.artifact_registry.repositories import (
    ArtifactRegistryRepositories,
)
from ai.backend.manager.repositories.auth.repositories import AuthRepositories
from ai.backend.manager.repositories.container_registry.repositories import (
    ContainerRegistryRepositories,
)
from ai.backend.manager.repositories.deployment.repositories import DeploymentRepositories
from ai.backend.manager.repositories.domain.repositories import DomainRepositories
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.huggingface_registry.repositories import (
    HuggingFaceRegistryRepositories,
)
from ai.backend.manager.repositories.image.repositories import ImageRepositories
from ai.backend.manager.repositories.keypair_resource_policy.repositories import (
    KeypairResourcePolicyRepositories,
)
from ai.backend.manager.repositories.metric.repositories import MetricRepositories
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.notification.repositories import NotificationRepositories
from ai.backend.manager.repositories.object_storage.repositories import ObjectStorageRepositories
from ai.backend.manager.repositories.permission_controller.repositories import (
    PermissionControllerRepositories,
)
from ai.backend.manager.repositories.project_resource_policy.repositories import (
    ProjectResourcePolicyRepositories,
)
from ai.backend.manager.repositories.reservoir_registry.repositories import (
    ReservoirRegistryRepositories,
)
from ai.backend.manager.repositories.resource_preset.repositories import ResourcePresetRepositories
from ai.backend.manager.repositories.scaling_group.repositories import ScalingGroupRepositories
from ai.backend.manager.repositories.schedule.repositories import ScheduleRepositories
from ai.backend.manager.repositories.scheduler.repositories import SchedulerRepositories
from ai.backend.manager.repositories.scheduling_history.repositories import (
    SchedulingHistoryRepositories,
)
from ai.backend.manager.repositories.session.repositories import SessionRepositories
from ai.backend.manager.repositories.storage_namespace.repositories import (
    StorageNamespaceRepositories,
)
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user.repositories import UserRepositories
from ai.backend.manager.repositories.user_resource_policy.repositories import (
    UserResourcePolicyRepositories,
)
from ai.backend.manager.repositories.vfolder.repositories import VfolderRepositories
from ai.backend.manager.repositories.vfs_storage.repositories import VFSStorageRepositories


@dataclass
class Repositories:
    agent: AgentRepositories
    app_config: AppConfigRepositories
    auth: AuthRepositories
    container_registry: ContainerRegistryRepositories
    deployment: DeploymentRepositories
    domain: DomainRepositories
    group: GroupRepositories
    image: ImageRepositories
    keypair_resource_policy: KeypairResourcePolicyRepositories
    metric: MetricRepositories
    model_serving: ModelServingRepositories
    notification: NotificationRepositories
    permission_controller: PermissionControllerRepositories
    project_resource_policy: ProjectResourcePolicyRepositories
    reservoir_registry: ReservoirRegistryRepositories
    resource_preset: ResourcePresetRepositories
    scaling_group: ScalingGroupRepositories
    schedule: ScheduleRepositories
    scheduler: SchedulerRepositories
    scheduling_history: SchedulingHistoryRepositories
    session: SessionRepositories
    user: UserRepositories
    user_resource_policy: UserResourcePolicyRepositories
    vfolder: VfolderRepositories
    object_storage: ObjectStorageRepositories
    vfs_storage: VFSStorageRepositories
    huggingface_registry: HuggingFaceRegistryRepositories
    artifact: ArtifactRepositories
    artifact_registry: ArtifactRegistryRepositories
    storage_namespace: StorageNamespaceRepositories

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        agent_repositories = AgentRepositories.create(args)
        app_config_repositories = AppConfigRepositories.create(args)
        auth_repositories = AuthRepositories.create(args)
        container_registry_repositories = ContainerRegistryRepositories.create(args)
        deployment_repositories = DeploymentRepositories.create(args)
        domain_repositories = DomainRepositories.create(args)
        group_repositories = GroupRepositories.create(args)
        image_repositories = ImageRepositories.create(args)
        keypair_resource_policy_repositories = KeypairResourcePolicyRepositories.create(args)
        metric_repositories = MetricRepositories.create(args)
        model_serving_repositories = ModelServingRepositories.create(args)
        notification_repositories = NotificationRepositories.create(args)
        permission_controller_repositories = PermissionControllerRepositories.create(args)
        project_resource_policy_repositories = ProjectResourcePolicyRepositories.create(args)
        reservoir_registry_repositories = ReservoirRegistryRepositories.create(args)
        resource_preset_repositories = ResourcePresetRepositories.create(args)
        scaling_group_repositories = ScalingGroupRepositories.create(args)
        schedule_repositories = ScheduleRepositories.create(args)
        scheduler_repositories = SchedulerRepositories.create(args)
        scheduling_history_repositories = SchedulingHistoryRepositories.create(args)
        session_repositories = SessionRepositories.create(args)
        user_repositories = UserRepositories.create(args)
        user_resource_policy_repositories = UserResourcePolicyRepositories.create(args)
        vfolder_repositories = VfolderRepositories.create(args)
        object_storage_repositories = ObjectStorageRepositories.create(args)
        vfs_storage_repositories = VFSStorageRepositories.create(args)
        artifact_repositories = ArtifactRepositories.create(args)
        huggingface_registry_repositories = HuggingFaceRegistryRepositories.create(args)
        artifact_registries = ArtifactRegistryRepositories.create(args)
        storage_namespace_repositories = StorageNamespaceRepositories.create(args)

        return cls(
            agent=agent_repositories,
            app_config=app_config_repositories,
            auth=auth_repositories,
            container_registry=container_registry_repositories,
            deployment=deployment_repositories,
            domain=domain_repositories,
            group=group_repositories,
            image=image_repositories,
            keypair_resource_policy=keypair_resource_policy_repositories,
            metric=metric_repositories,
            model_serving=model_serving_repositories,
            notification=notification_repositories,
            permission_controller=permission_controller_repositories,
            project_resource_policy=project_resource_policy_repositories,
            reservoir_registry=reservoir_registry_repositories,
            resource_preset=resource_preset_repositories,
            scaling_group=scaling_group_repositories,
            schedule=schedule_repositories,
            scheduler=scheduler_repositories,
            scheduling_history=scheduling_history_repositories,
            session=session_repositories,
            user=user_repositories,
            user_resource_policy=user_resource_policy_repositories,
            vfolder=vfolder_repositories,
            object_storage=object_storage_repositories,
            vfs_storage=vfs_storage_repositories,
            huggingface_registry=huggingface_registry_repositories,
            artifact=artifact_repositories,
            artifact_registry=artifact_registries,
            storage_namespace=storage_namespace_repositories,
        )

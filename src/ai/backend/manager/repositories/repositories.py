from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repositories import AgentRepositories
from ai.backend.manager.repositories.auth.repositories import AuthRepositories
from ai.backend.manager.repositories.container_registry.repositories import (
    ContainerRegistryRepositories,
)
from ai.backend.manager.repositories.domain.repositories import DomainRepositories
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.image.repositories import ImageRepositories
from ai.backend.manager.repositories.keypair_resource_policy.repositories import (
    KeypairResourcePolicyRepositories,
)
from ai.backend.manager.repositories.metric.repositories import MetricRepositories
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.project_resource_policy.repositories import (
    ProjectResourcePolicyRepositories,
)
from ai.backend.manager.repositories.resource_preset.repositories import ResourcePresetRepositories
from ai.backend.manager.repositories.schedule.repositories import ScheduleRepositories
from ai.backend.manager.repositories.session.repositories import SessionRepositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user.repositories import UserRepositories
from ai.backend.manager.repositories.user_resource_policy.repositories import (
    UserResourcePolicyRepositories,
)
from ai.backend.manager.repositories.vfolder.repositories import VfolderRepositories


@dataclass
class Repositories:
    agent: AgentRepositories
    auth: AuthRepositories
    container_registry: ContainerRegistryRepositories
    domain: DomainRepositories
    group: GroupRepositories
    image: ImageRepositories
    keypair_resource_policy: KeypairResourcePolicyRepositories
    metric: MetricRepositories
    model_serving: ModelServingRepositories
    project_resource_policy: ProjectResourcePolicyRepositories
    resource_preset: ResourcePresetRepositories
    schedule: ScheduleRepositories
    session: SessionRepositories
    user: UserRepositories
    user_resource_policy: UserResourcePolicyRepositories
    vfolder: VfolderRepositories

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        agent_repositories = AgentRepositories.create(args)
        auth_repositories = AuthRepositories.create(args)
        container_registry_repositories = ContainerRegistryRepositories.create(args)
        domain_repositories = DomainRepositories.create(args)
        group_repositories = GroupRepositories.create(args)
        image_repositories = ImageRepositories.create(args)
        keypair_resource_policy_repositories = KeypairResourcePolicyRepositories.create(args)
        metric_repositories = MetricRepositories.create(args)
        model_serving_repositories = ModelServingRepositories.create(args)
        project_resource_policy_repositories = ProjectResourcePolicyRepositories.create(args)
        resource_preset_repositories = ResourcePresetRepositories.create(args)
        schedule_repositories = ScheduleRepositories.create(args)
        session_repositories = SessionRepositories.create(args)
        user_repositories = UserRepositories.create(args)
        user_resource_policy_repositories = UserResourcePolicyRepositories.create(args)
        vfolder_repositories = VfolderRepositories.create(args)

        return cls(
            agent=agent_repositories,
            auth=auth_repositories,
            container_registry=container_registry_repositories,
            domain=domain_repositories,
            group=group_repositories,
            image=image_repositories,
            keypair_resource_policy=keypair_resource_policy_repositories,
            metric=metric_repositories,
            model_serving=model_serving_repositories,
            project_resource_policy=project_resource_policy_repositories,
            resource_preset=resource_preset_repositories,
            schedule=schedule_repositories,
            session=session_repositories,
            user=user_repositories,
            user_resource_policy=user_resource_policy_repositories,
            vfolder=vfolder_repositories,
        )

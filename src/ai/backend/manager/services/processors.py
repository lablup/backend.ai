from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


class Processors:
    agent: AgentProcessors
    user: UserProcessors
    group: GroupProcessors
    resource_preset: ResourcePresetProcessors
    container_registry: ContainerRegistryProcessors
    keypair_resource_policy: KeypairResourcePolicyProcessors
    user_resource_policy: UserResourcePolicyProcessors
    project_resource_policy: ProjectResourcePolicyProcessors

    def __init__(
        self,
        agent_service: AgentService,
        user_service: UserService,
        group_service: GroupService,
        resource_preset_service: ResourcePresetService,
        container_registry_service: ContainerRegistryService,
        keypair_resource_policy_service: KeypairResourcePolicyService,
        user_resource_policy_service: UserResourcePolicyService,
        project_resource_policy_service: ProjectResourcePolicyService,
    ) -> None:
        self.agent = AgentProcessors(agent_service)
        self.user = UserProcessors(user_service)
        self.group = GroupProcessors(group_service)
        self.resource_preset = ResourcePresetProcessors(resource_preset_service)
        self.container_registry = ContainerRegistryProcessors(container_registry_service)
        self.keypair_resource_policy = KeypairResourcePolicyProcessors(
            keypair_resource_policy_service
        )
        self.user_resource_policy = UserResourcePolicyProcessors(user_resource_policy_service)
        self.project_resource_policy = ProjectResourcePolicyProcessors(
            project_resource_policy_service
        )

from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.groups.processors import GroupProcessors
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.metric.processors.container import (
    MetricProcessors as ContainerMetricProcessors,
)
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.vfolder.processors import (
    VFolderBaseProcessors,
    VFolderFileProcessors,
    VFolderInviteProcessors,
)


class Processors:
    agent: AgentProcessors
    domain: DomainProcessors
    group: GroupProcessors
    user: UserProcessors
    image: ImageProcessors
    container_registry: ContainerRegistryProcessors
    keypair_resource_policy: KeypairResourcePolicyProcessors
    user_resource_policy: UserResourcePolicyProcessors
    project_resource_policy: ProjectResourcePolicyProcessors
    resource_preset: ResourcePresetProcessors

    vfolder: VFolderBaseProcessors
    vfolder_invitation: VFolderInviteProcessors
    vfolder_file: VFolderFileProcessors
    session: SessionProcessors

    container_metric: ContainerMetricProcessors

    def __init__(
        self,
        agent: AgentProcessors,
        domain: DomainProcessors,
        group: GroupProcessors,
        user: UserProcessors,
        image: ImageProcessors,
        container_registry: ContainerRegistryProcessors,
        vfolder: VFolderBaseProcessors,
        vfolder_invite: VFolderInviteProcessors,
        vfolder_file: VFolderFileProcessors,
        session: SessionProcessors,
        keypair_resource_policy: KeypairResourcePolicyProcessors,
        user_resource_policy: UserResourcePolicyProcessors,
        project_resource_policy: ProjectResourcePolicyProcessors,
        resource_preset: ResourcePresetProcessors,
        container_metric: ContainerMetricProcessors,
    ) -> None:
        self.agent = agent
        self.domain = domain
        self.group = group
        self.user = user
        self.image = image
        self.container_registry = container_registry
        self.vfolder = vfolder
        self.vfolder_invitation = vfolder_invite
        self.vfolder_file = vfolder_file
        self.session = session
        self.keypair_resource_policy = keypair_resource_policy
        self.user_resource_policy = user_resource_policy
        self.project_resource_policy = project_resource_policy
        self.resource_preset = resource_preset
        self.container_metric = container_metric

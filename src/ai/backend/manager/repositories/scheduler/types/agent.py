"""Agent related types."""

from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.sokovan.agent import AgentInfo, AgentResource


@dataclass
class AgentMeta:
    """Agent metadata plus normalized per-slot resources."""

    id: AgentId
    addr: str
    architecture: str
    resources: AgentResource
    container_count: int
    resource_group_id: ResourceGroupID
    scaling_group: str

    def to_agent_info(self) -> AgentInfo:
        return AgentInfo(
            agent_id=self.id,
            agent_addr=self.addr,
            architecture=self.architecture,
            resources=self.resources,
            scaling_group=self.scaling_group,
            container_count=self.container_count,
        )

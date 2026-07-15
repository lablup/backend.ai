"""Agent related types."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.sokovan.agent import AgentInfo
from ai.backend.manager.data.sokovan.snapshot import AgentOccupancy


@dataclass
class AgentMeta:
    """Agent metadata without cached occupancy values."""

    id: AgentId
    addr: str
    architecture: str
    available_slots: ResourceSlot
    resource_group_id: ResourceGroupID
    scaling_group: str

    def to_agent_info(
        self,
        occupancy_map: Mapping[AgentId, AgentOccupancy],
    ) -> AgentInfo:
        occupancy = occupancy_map.get(self.id)
        if occupancy:
            occupied = ResourceSlot({sq.slot_name: sq.quantity for sq in occupancy.occupied_slots})
        else:
            occupied = ResourceSlot()
        return AgentInfo(
            agent_id=self.id,
            agent_addr=self.addr,
            architecture=self.architecture,
            scaling_group=self.scaling_group,
            available_slots=self.available_slots,
            occupied_slots=occupied,
            container_count=occupancy.container_count if occupancy else 0,
        )

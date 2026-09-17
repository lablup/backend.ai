"""Write specs for an agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import (
    AgentHeartbeatUpsert,
    AgentMetadata,
    AgentNetworkInfo,
    AgentResourceInfo,
    AgentStatus,
)
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.agent.upserters import AgentHeartbeatUpserter
from bai_scenario.seeds.seeder import Naming, SeedRowFrom


@dataclass(frozen=True)
class SeedAgent(SeedRowFrom[ResourceGroupData, AgentUUID]):
    """An agent of the given resource group, registered the way its first heartbeat
    registers it. It reports no slot; the slots it carries are laid under it."""

    name_hint: str = "agent"

    @override
    def kind(self) -> str:
        return "에이전트"

    @override
    def detail(self) -> str:
        return "살아 있고, 아직 보고한 슬롯이 없다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: ResourceGroupData) -> AgentHeartbeatUpserter:
        return AgentHeartbeatUpserter(
            upsert_data=AgentHeartbeatUpsert(
                metadata=AgentMetadata(
                    id=AgentId(name),
                    status=AgentStatus.ALIVE,
                    region="local",
                    resource_group=source.name,
                    architecture="x86_64",
                    version="0.0.0",
                    auto_terminate_abusing_kernel=False,
                ),
                network_info=AgentNetworkInfo(
                    addr=f"tcp://{name}:6001", public_host=name, public_key=None
                ),
                resource_info=AgentResourceInfo(
                    slot_key_and_units={}, available_slots=ResourceSlot(), compute_plugins={}
                ),
                lost_at=None,
                heartbeat_received=datetime.now(UTC),
            ),
            resource_group_id=source.id,
            resource_group_name=source.name,
        )

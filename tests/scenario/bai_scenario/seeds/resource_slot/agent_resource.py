"""Write specs for the slots an agent reports."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.resource_slot.upserters import AgentResourceUpserter
from bai_scenario.seeds.seeder import TestSeedFieldUpserter


@dataclass(frozen=True)
class TestSeedReportedSlot(TestSeedFieldUpserter[AgentUUID, AgentResourceData]):
    """One slot an agent reports. Only the scheduler writes the reserved amounts, so a
    reported slot holds none."""

    agent_id: str
    slot_name: str
    capacity: Decimal
    used: Decimal

    @override
    def kind(self) -> str:
        return f"{self.slot_name} 슬롯 용량 {self.capacity} 보고, {self.used} 사용 중"

    @override
    def owner_id(self, owner: AgentUUID) -> AgentUUID:
        return owner

    @override
    def seed(self) -> AgentResourceUpserter:
        return AgentResourceUpserter(
            agent_id=self.agent_id,
            slot_name=self.slot_name,
            capacity=self.capacity,
            used=self.used,
        )

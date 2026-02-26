"""CreatorSpec implementations for agent entities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class AgentCreatorSpec(CreatorSpec[AgentRow]):
    """CreatorSpec for agent registration."""

    id: AgentId
    region: str
    scaling_group: str
    addr: str
    architecture: str
    version: str
    available_slots: ResourceSlot
    compute_plugins: Mapping[str, Any]
    status: AgentStatus = AgentStatus.ALIVE
    schedulable: bool = True
    auto_terminate_abusing_kernel: bool = False

    @override
    def build_row(self) -> AgentRow:
        return AgentRow(
            id=str(self.id),
            status=self.status,
            region=self.region,
            scaling_group=self.scaling_group,
            addr=self.addr,
            architecture=self.architecture,
            version=self.version,
            available_slots=self.available_slots,
            occupied_slots=ResourceSlot(),
            compute_plugins=dict(self.compute_plugins),
            schedulable=self.schedulable,
            auto_terminate_abusing_kernel=self.auto_terminate_abusing_kernel,
        )

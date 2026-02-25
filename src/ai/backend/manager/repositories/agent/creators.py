"""CreatorSpec implementations for agent repository."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class AgentCreatorSpec(CreatorSpec[AgentRow]):
    """CreatorSpec for agent creation during heartbeat registration."""

    id: AgentId
    region: str | None
    scaling_group: str
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    addr: str
    public_host: str | None
    public_key: PublicKey | None
    version: str
    architecture: str
    compute_plugins: dict[str, Any]
    auto_terminate_abusing_kernel: bool
    first_contact: datetime
    status: AgentStatus

    @override
    def build_row(self) -> AgentRow:
        return AgentRow(
            id=self.id,
            status=self.status,
            region=self.region,
            scaling_group=self.scaling_group,
            available_slots=self.available_slots,
            occupied_slots=self.occupied_slots,
            addr=self.addr,
            public_host=self.public_host,
            public_key=self.public_key,
            version=self.version,
            architecture=self.architecture,
            compute_plugins=self.compute_plugins,
            auto_terminate_abusing_kernel=self.auto_terminate_abusing_kernel,
            first_contact=self.first_contact,
            lost_at=None,
        )

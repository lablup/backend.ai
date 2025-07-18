from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models.agent import AgentRow, AgentStatus


@dataclass
class AgentData:
    id: AgentId
    status: AgentStatus
    status_changed: Optional[datetime]
    region: str
    scaling_group: str
    schedulable: bool
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    addr: str
    public_host: Optional[str]
    first_contact: datetime
    lost_at: Optional[datetime]
    version: str
    architecture: str
    compute_plugins: list[str]

    @classmethod
    def from_row(cls, row: AgentRow) -> Self:
        return cls(
            id=row.id,
            status=row.status,
            status_changed=row.status_changed,
            region=row.region,
            scaling_group=row.scaling_group,
            schedulable=row.schedulable,
            available_slots=row.available_slots,
            occupied_slots=row.occupied_slots,
            addr=row.addr,
            public_host=row.public_host,
            first_contact=row.first_contact,
            lost_at=row.lost_at,
            version=row.version,
            architecture=row.architecture,
            compute_plugins=row.compute_plugins,
        )

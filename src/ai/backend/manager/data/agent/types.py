from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.common.types import AgentId, ResourceSlot

from ..kernel.types import KernelInfo, KernelStatus


class AgentStatus(enum.Enum):
    ALIVE = 0
    LOST = 1
    RESTARTING = 2
    TERMINATED = 3

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Optional[AgentStatus]:
        if isinstance(value, int):
            for member in cls:
                if member.value == value:
                    return member
        if isinstance(value, str):
            match value.upper():
                case "ALIVE":
                    return cls.ALIVE
                case "LOST":
                    return cls.LOST
                case "RESTARTING":
                    return cls.RESTARTING
                case "TERMINATED":
                    return cls.TERMINATED
        return None


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
    auto_terminate_abusing_kernel: bool


@dataclass
class AgentDataExtended(AgentData):
    kernels: list[KernelInfo]

    def running_kernel_occupied_slots(self) -> ResourceSlot:
        total = ResourceSlot()
        for kernel in self.kernels:
            if kernel.lifecycle.status == KernelStatus.RUNNING:
                total += kernel.resource.occupied_slots
        return total

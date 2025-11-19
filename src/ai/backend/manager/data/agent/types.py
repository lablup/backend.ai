from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Self, override

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.types import AgentId, DeviceName, ResourceSlot, SlotName, SlotTypes

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

    @classmethod
    def unavailable_statuses(cls) -> tuple[AgentStatus, ...]:
        """
        Return agent statuses that indicate the agent is unavailable for kernel operations.
        These agents cannot handle kernel termination or other operations.
        """
        return (cls.LOST, cls.TERMINATED)


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
    public_key: Optional[PublicKey]
    auto_terminate_abusing_kernel: bool


@dataclass
class AgentDataExtended(AgentData):
    known_slot_types: Mapping[SlotName, SlotTypes]
    kernels: list[KernelInfo]

    def running_kernel_occupied_slots(self) -> ResourceSlot:
        occupied_slots = ResourceSlot.from_known_slots(self.known_slot_types)
        for kernel in self.kernels:
            if kernel.lifecycle.status == KernelStatus.RUNNING:
                occupied_slots += kernel.resource.occupied_slots
        return occupied_slots


@dataclass
class AgentMetadata:
    id: AgentId
    status: AgentStatus
    region: Optional[str]
    scaling_group: str
    architecture: str
    version: str
    auto_terminate_abusing_kernel: bool


@dataclass
class AgentNetworkInfo:
    addr: str
    public_host: str
    public_key: Optional[PublicKey]


@dataclass
class AgentResourceInfo:
    slot_key_and_units: dict[SlotName, SlotTypes]
    available_slots: ResourceSlot
    compute_plugins: Mapping[DeviceName, Mapping[str, str]]


@dataclass
class AgentHeartbeatUpsert:
    metadata: AgentMetadata
    network_info: AgentNetworkInfo
    resource_info: AgentResourceInfo
    lost_at: Optional[datetime]
    heartbeat_received: datetime

    @property
    def insert_fields(self) -> dict[str, Any]:
        return {
            "id": self.metadata.id,
            "status": AgentStatus.ALIVE,
            "region": self.metadata.region,
            "scaling_group": self.metadata.scaling_group,
            "available_slots": self.resource_info.available_slots,
            "addr": self.network_info.addr,
            "public_host": self.network_info.public_host,
            "public_key": self.network_info.public_key,
            "version": self.metadata.version,
            "compute_plugins": self.resource_info.compute_plugins,
            "architecture": self.metadata.architecture,
            "auto_terminate_abusing_kernel": self.metadata.auto_terminate_abusing_kernel,
            "lost_at": None,
            "occupied_slots": {},
            "first_contact": self.heartbeat_received,
        }

    @property
    def update_fields(self) -> dict[str, Any]:
        return {
            "id": self.metadata.id,
            "status": AgentStatus.ALIVE,
            "region": self.metadata.region,
            "scaling_group": self.metadata.scaling_group,
            "available_slots": self.resource_info.available_slots,
            "addr": self.network_info.addr,
            "public_host": self.network_info.public_host,
            "public_key": self.network_info.public_key,
            "version": self.metadata.version,
            "compute_plugins": self.resource_info.compute_plugins,
            "architecture": self.metadata.architecture,
            "auto_terminate_abusing_kernel": self.metadata.auto_terminate_abusing_kernel,
            "lost_at": None,
        }

    @classmethod
    def from_agent_info(
        cls, agent_id: AgentId, agent_info: AgentInfo, heartbeat_received: datetime
    ) -> Self:
        return cls(
            metadata=AgentMetadata(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region=agent_info.region,
                scaling_group=agent_info.scaling_group,
                architecture=agent_info.architecture,
                auto_terminate_abusing_kernel=agent_info.auto_terminate_abusing_kernel,
                version=agent_info.version,
            ),
            network_info=AgentNetworkInfo(
                addr=agent_info.addr,
                public_host=agent_info.public_host,
                public_key=agent_info.public_key,
            ),
            resource_info=AgentResourceInfo(
                slot_key_and_units=agent_info.slot_key_and_units,
                available_slots=agent_info.available_resource_slots,
                compute_plugins=agent_info.compute_plugins,
            ),
            lost_at=None,
            heartbeat_received=heartbeat_received,
        )


@dataclass
class UpsertResult:
    was_revived: bool
    need_resource_slot_update: bool

    @classmethod
    def from_state_comparison(
        cls, existing_data: Optional[AgentData], upsert_data: AgentHeartbeatUpsert
    ) -> Self:
        if existing_data is None:
            return cls(
                was_revived=False,
                need_resource_slot_update=True,
            )

        was_revived = existing_data.status in (AgentStatus.LOST, AgentStatus.TERMINATED)
        need_resource_slot_update = (
            existing_data.available_slots != upsert_data.resource_info.available_slots
            or existing_data.scaling_group != upsert_data.metadata.scaling_group
            or existing_data.addr != upsert_data.network_info.addr
            or existing_data.public_host != upsert_data.network_info.public_host
            or existing_data.public_key != upsert_data.network_info.public_key
            or existing_data.version != upsert_data.metadata.version
            or existing_data.compute_plugins != upsert_data.resource_info.compute_plugins
            or existing_data.architecture != upsert_data.metadata.architecture
            or existing_data.auto_terminate_abusing_kernel
            != upsert_data.metadata.auto_terminate_abusing_kernel
        )
        return cls(
            was_revived=was_revived,
            need_resource_slot_update=need_resource_slot_update,
        )

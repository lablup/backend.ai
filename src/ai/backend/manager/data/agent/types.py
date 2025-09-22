from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Self

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import AgentId, DeviceName, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.models.agent import AgentStatus

if TYPE_CHECKING:
    from sqlalchemy.engine import Row


@dataclass
class AgentStateSyncData:
    now: datetime
    slot_key_and_units: dict[SlotName, SlotTypes]
    current_addr: str
    public_key: PublicKey


@dataclass
class AgentMetadata:
    id: AgentId
    status: AgentStatus
    region: str
    scaling_group: str
    architecture: str
    version: str
    auto_terminate_abusing_kernel: bool


@dataclass
class AgentNetworkInfo:
    addr: str
    public_host: str
    public_key: PublicKey


@dataclass
class AgentResourceInfo:
    available_slots: ResourceSlot
    compute_plugins: Mapping[DeviceName, Mapping[str, str]]


@dataclass
class AgentHeartbeatUpsert:
    metadata: AgentMetadata
    network_info: AgentNetworkInfo
    resource_info: AgentResourceInfo
    lost_at: Optional[datetime]
    first_contact: datetime

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
            "first_contact": self.first_contact,
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
        cls, agent_id: AgentId, agent_info: Mapping[Any, Any], heartbeat_received: datetime
    ) -> Self:
        return cls(
            metadata=AgentMetadata(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region=agent_info["region"],
                scaling_group=agent_info.get("scaling_group", "default"),
                architecture=agent_info.get("architecture", "x86_64"),
                auto_terminate_abusing_kernel=agent_info.get(
                    "auto_terminate_abusing_kernel", False
                ),
                version=agent_info["version"],
            ),
            network_info=AgentNetworkInfo(
                addr=agent_info["addr"],
                public_host=agent_info["public_host"],
                public_key=agent_info["public_key"],
            ),
            resource_info=AgentResourceInfo(
                available_slots=ResourceSlot({
                    SlotName(k): Decimal(v[1]) for k, v in agent_info["resource_slots"].items()
                }),
                compute_plugins=agent_info["compute_plugins"],
            ),
            lost_at=None,
            first_contact=heartbeat_received,
        )


@dataclass
class UpsertResult:
    was_insert: bool
    was_revived: bool
    need_resource_slot_update: bool

    @classmethod
    def from_state_comparison(
        cls, existing_row: Optional["Row"], upsert_data: "AgentHeartbeatUpsert"
    ) -> Self:
        if existing_row is None:
            return cls(
                was_insert=True,
                was_revived=False,
                need_resource_slot_update=True,
            )

        was_revived = existing_row.status in (AgentStatus.LOST, AgentStatus.TERMINATED)
        need_resource_slot_update = (
            existing_row.available_slots != upsert_data.resource_info.available_slots
            or existing_row.scaling_group != upsert_data.metadata.scaling_group
            or existing_row.addr != upsert_data.network_info.addr
            or existing_row.public_host != upsert_data.network_info.public_host
            or existing_row.public_key != upsert_data.network_info.public_key
            or existing_row.version != upsert_data.metadata.version
            or existing_row.compute_plugins != upsert_data.resource_info.compute_plugins
            or existing_row.architecture != upsert_data.metadata.architecture
            or existing_row.auto_terminate_abusing_kernel
            != upsert_data.metadata.auto_terminate_abusing_kernel
        )
        return cls(
            was_insert=False,
            was_revived=was_revived,
            need_resource_slot_update=need_resource_slot_update,
        )

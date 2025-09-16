from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import AgentId, ResourceSlot, SlotName, SlotTypes
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
class AgentHeartbeatUpsert:
    id: AgentId
    status: AgentStatus
    region: str
    scaling_group: str
    available_slots: ResourceSlot
    addr: str
    public_host: str
    public_key: str
    version: str
    compute_plugins: dict[Any, Any]
    architecture: str
    auto_terminate_abusing_kernel: bool
    lost_at: Optional[datetime]
    first_contact: datetime

    @property
    def insert_fields(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": AgentStatus.ALIVE,
            "region": self.region,
            "scaling_group": self.scaling_group,
            "available_slots": self.available_slots,
            "addr": self.addr,
            "public_host": self.public_host,
            "public_key": self.public_key,
            "version": self.version,
            "compute_plugins": self.compute_plugins,
            "architecture": self.architecture,
            "auto_terminate_abusing_kernel": self.auto_terminate_abusing_kernel,
            "lost_at": None,
            "occupied_slots": {},
            "first_contact": self.first_contact,
        }

    @property
    def update_fields(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": AgentStatus.ALIVE,
            "region": self.region,
            "scaling_group": self.scaling_group,
            "available_slots": self.available_slots,
            "addr": self.addr,
            "public_host": self.public_host,
            "public_key": self.public_key,
            "version": self.version,
            "compute_plugins": self.compute_plugins,
            "architecture": self.architecture,
            "auto_terminate_abusing_kernel": self.auto_terminate_abusing_kernel,
            "lost_at": None,
        }

    @classmethod
    def from_agent_info(
        cls, agent_id: AgentId, agent_info: Mapping[Any, Any], heartbeat_received: datetime
    ) -> "AgentHeartbeatUpsert":
        return cls(
            id=agent_id,
            status=AgentStatus.ALIVE,
            region=agent_info["region"],
            scaling_group=agent_info.get("scaling_group", "default"),
            available_slots=ResourceSlot({
                SlotName(k): Decimal(v[1]) for k, v in agent_info["resource_slots"].items()
            }),
            addr=agent_info["addr"],
            public_host=agent_info["public_host"],
            public_key=agent_info["public_key"],
            version=agent_info["version"],
            compute_plugins=agent_info["compute_plugins"],
            architecture=agent_info.get("architecture", "x86_64"),
            auto_terminate_abusing_kernel=agent_info.get("auto_terminate_abusing_kernel", False),
            lost_at=None,
            first_contact=heartbeat_received,
        )


@dataclass
class UpsertResult:
    was_insert: bool
    was_revived: bool
    need_agent_cache_update: bool
    need_resource_slot_update: bool

    @classmethod
    def from_state_comparison(
        cls, existing_row: Optional["Row"], upsert_data: "AgentHeartbeatUpsert"
    ) -> "UpsertResult":
        if existing_row is None:
            return cls(
                was_insert=True,
                was_revived=False,
                need_agent_cache_update=True,
                need_resource_slot_update=True,
            )

        was_revived = existing_row.status in (AgentStatus.LOST, AgentStatus.TERMINATED)
        need_agent_cache_update = (
            existing_row.addr != upsert_data.addr
            or existing_row.public_key != upsert_data.public_key
        )
        need_resource_slot_update = (
            existing_row.available_slots != upsert_data.available_slots
            or existing_row.scaling_group != upsert_data.scaling_group
            or existing_row.addr != upsert_data.addr
            or existing_row.public_host != upsert_data.public_host
            or existing_row.public_key != upsert_data.public_key
            or existing_row.version != upsert_data.version
            or existing_row.compute_plugins != upsert_data.compute_plugins
            or existing_row.architecture != upsert_data.architecture
            or existing_row.auto_terminate_abusing_kernel
            != upsert_data.auto_terminate_abusing_kernel
        )
        return cls(
            was_insert=False,
            was_revived=was_revived,
            need_agent_cache_update=need_agent_cache_update,
            need_resource_slot_update=need_resource_slot_update,
        )

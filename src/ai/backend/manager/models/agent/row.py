from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.expression import false, true

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentDataForHeartbeatUpdate,
    AgentStatus,
)
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    CurvePublicKeyColumn,
    EnumType,
)
from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__: Sequence[str] = (
    "AgentRow",
    "agents",
    "list_schedulable_agents_by_sgroup",
)


class AgentRow(Base):
    __tablename__ = "agents"

    uuid: Mapped[AgentUUID] = mapped_column(
        "uuid",
        GUID(AgentUUID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v7()"),
    )
    id: Mapped[AgentId] = mapped_column("id", sa.String(length=64), primary_key=True)
    status: Mapped[AgentStatus] = mapped_column(
        "status", EnumType(AgentStatus), nullable=False, index=True, default=AgentStatus.ALIVE
    )
    status_changed: Mapped[datetime | None] = mapped_column(
        "status_changed", sa.DateTime(timezone=True), nullable=True
    )
    region: Mapped[str] = mapped_column("region", sa.String(length=64), index=True, nullable=False)
    scaling_group: Mapped[str] = mapped_column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name"),
        index=True,
        nullable=False,
        server_default="default",
        default="default",
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        sa.ForeignKey("scaling_groups.id"),
        index=True,
        nullable=False,
    )
    schedulable: Mapped[bool] = mapped_column(
        "schedulable", sa.Boolean(), nullable=False, server_default=true(), default=True
    )
    addr: Mapped[str] = mapped_column("addr", sa.String(length=128), nullable=False)
    public_host: Mapped[str | None] = mapped_column(
        "public_host", sa.String(length=256), nullable=True
    )
    public_key: Mapped[PublicKey | None] = mapped_column(
        "public_key", CurvePublicKeyColumn(), nullable=True
    )
    first_contact: Mapped[datetime | None] = mapped_column(
        "first_contact", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    lost_at: Mapped[datetime | None] = mapped_column(
        "lost_at", sa.DateTime(timezone=True), nullable=True
    )
    version: Mapped[str] = mapped_column("version", sa.String(length=64), nullable=False)
    architecture: Mapped[str] = mapped_column("architecture", sa.String(length=32), nullable=False)
    compute_plugins: Mapped[dict[str, Any]] = mapped_column(
        "compute_plugins", pgsql.JSONB(), nullable=False, default={}
    )
    auto_terminate_abusing_kernel: Mapped[bool] = mapped_column(
        "auto_terminate_abusing_kernel",
        sa.Boolean(),
        nullable=False,
        server_default=false(),
        default=False,
    )

    agent_resource_rows: Mapped[list[AgentResourceRow]] = relationship("AgentResourceRow")

    def _resource_rows_by_rank(self) -> list[AgentResourceRow]:
        return sorted(self.agent_resource_rows, key=lambda r: r.slot_type_row.rank)

    def resources_by_rank(self) -> list[AgentResourceData]:
        return [resource_row.to_data() for resource_row in self._resource_rows_by_rank()]

    def actual_available_slots(self) -> ResourceSlot:
        available = ResourceSlot()
        for resource_row in self._resource_rows_by_rank():
            available[resource_row.slot_name] = resource_row.capacity
        return available

    def actual_occupied_slots(self) -> ResourceSlot:
        occupied = ResourceSlot()
        for resource_row in self._resource_rows_by_rank():
            occupied[resource_row.slot_name] = resource_row.used
        return occupied

    def to_data(self) -> AgentData:
        return AgentData(
            uuid=self.uuid,
            id=AgentId(self.id),
            status=self.status,
            status_changed=self.status_changed,
            region=self.region,
            resource_group=self.scaling_group,
            schedulable=self.schedulable,
            addr=self.addr,
            public_host=self.public_host,
            first_contact=self.first_contact,
            lost_at=self.lost_at,
            version=self.version,
            architecture=self.architecture,
            compute_plugins=self.compute_plugins,
            public_key=self.public_key,
            auto_terminate_abusing_kernel=self.auto_terminate_abusing_kernel,
        )

    def to_heartbeat_update_data(self) -> AgentDataForHeartbeatUpdate:
        return AgentDataForHeartbeatUpdate(
            status=self.status,
            status_changed=self.status_changed,
            available_slots=self.actual_available_slots(),
            addr=self.addr,
            public_host=self.public_host,
            version=self.version,
            architecture=self.architecture,
            compute_plugins=self.compute_plugins,
            public_key=self.public_key,
            auto_terminate_abusing_kernel=self.auto_terminate_abusing_kernel,
        )

    @classmethod
    async def get_occupied_slots(
        cls,
        db: ExtendedAsyncSAEngine,
        agent_id: AgentId,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourceSlot:
        async with db.begin_readonly_session() as db_session:
            query = sa.select(AgentResourceRow.slot_name, AgentResourceRow.used).where(
                AgentResourceRow.agent_id == agent_id,
            )
            result = await db_session.execute(query)
            occupied_slots = ResourceSlot.from_known_slots(known_slot_types)
            for row in result:
                occupied_slots[row.slot_name] = row.used
            return occupied_slots


# For compatibility
agents = AgentRow.__table__


async def list_schedulable_agents_by_sgroup(
    db_sess: SASession,
    sgroup_name: str,
) -> Sequence[AgentRow]:
    query = sa.select(AgentRow).where(
        (AgentRow.status == AgentStatus.ALIVE)
        & (AgentRow.scaling_group == sgroup_name)
        & (AgentRow.schedulable == true()),
    )

    result = await db_sess.execute(query)
    return result.scalars().all()

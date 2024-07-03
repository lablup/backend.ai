from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, cast

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import relationship, selectinload, with_loader_criteria
from sqlalchemy.sql.expression import false, true

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import AgentId, BinarySize, HardwareMetadata, ResourceSlot

from .base import (
    Base,
    CurvePublicKeyColumn,
    EnumType,
    Item,
    PaginatedList,
    ResourceSlotColumn,
    batch_result,
    mapper_registry,
    privileged_mutation,
    set_if_set,
    simple_db_mutate,
)
from .group import association_groups_users
from .kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, KernelRow, kernels
from .keypair import keypairs
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from .scaling_group import query_allowed_sgroups
from .user import UserRole, users

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext


__all__: Sequence[str] = (
    "agents",
    "AgentRow",
    "AgentStatus",
    "AgentList",
    "Agent",
    "AgentSummary",
    "AgentSummaryList",
    "ModifyAgent",
    "recalc_agent_resource_occupancy",
    "list_schedulable_agents_by_sgroup",
)


class AgentStatus(enum.Enum):
    ALIVE = 0
    LOST = 1
    RESTARTING = 2
    TERMINATED = 3


agents = sa.Table(
    "agents",
    mapper_registry.metadata,
    sa.Column("id", sa.String(length=64), primary_key=True),
    sa.Column(
        "status", EnumType(AgentStatus), nullable=False, index=True, default=AgentStatus.ALIVE
    ),
    sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True),
    sa.Column("region", sa.String(length=64), index=True, nullable=False),
    sa.Column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name"),
        index=True,
        nullable=False,
        server_default="default",
        default="default",
    ),
    sa.Column("schedulable", sa.Boolean(), nullable=False, server_default=true(), default=True),
    sa.Column("available_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("addr", sa.String(length=128), nullable=False),
    sa.Column("public_host", sa.String(length=256), nullable=True),
    sa.Column("public_key", CurvePublicKeyColumn(), nullable=True),
    sa.Column("first_contact", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("version", sa.String(length=64), nullable=False),
    sa.Column("architecture", sa.String(length=32), nullable=False),
    sa.Column("compute_plugins", pgsql.JSONB(), nullable=False, default={}),
    sa.Column(
        "auto_terminate_abusing_kernel",
        sa.Boolean(),
        nullable=False,
        server_default=false(),
        default=False,
    ),
)


class AgentRow(Base):
    __table__ = agents
    kernels = relationship("KernelRow", back_populates="agent_row")
    scaling_group_row = relationship("ScalingGroupRow", back_populates="agents")


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


class Agent(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    status = graphene.String()
    status_changed = GQLDateTime()
    region = graphene.String()
    scaling_group = graphene.String()
    schedulable = graphene.Boolean()
    available_slots = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    addr = graphene.String()  # bind/advertised host:port
    architecture = graphene.String()
    first_contact = GQLDateTime()
    lost_at = GQLDateTime()
    live_stat = graphene.JSONString()
    version = graphene.String()
    compute_plugins = graphene.JSONString()
    hardware_metadata = graphene.JSONString()
    auto_terminate_abusing_kernel = graphene.Boolean()
    local_config = graphene.JSONString()
    container_count = graphene.Int()

    # Legacy fields
    mem_slots = graphene.Int()
    cpu_slots = graphene.Float()
    gpu_slots = graphene.Float()
    tpu_slots = graphene.Float()
    used_mem_slots = graphene.Int()
    used_cpu_slots = graphene.Float()
    used_gpu_slots = graphene.Float()
    used_tpu_slots = graphene.Float()
    cpu_cur_pct = graphene.Float()
    mem_cur_bytes = graphene.Float()

    compute_containers = graphene.List(
        "ai.backend.manager.models.ComputeContainer", status=graphene.String()
    )

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> Agent:
        mega = 2**20
        return cls(
            id=row["id"],
            status=row["status"].name,
            status_changed=row["status_changed"],
            region=row["region"],
            scaling_group=row["scaling_group"],
            schedulable=row["schedulable"],
            available_slots=row["available_slots"].to_json(),
            occupied_slots=row["occupied_slots"].to_json(),
            addr=row["addr"],
            architecture=row["architecture"],
            first_contact=row["first_contact"],
            lost_at=row["lost_at"],
            version=row["version"],
            compute_plugins=row["compute_plugins"],
            auto_terminate_abusing_kernel=row["auto_terminate_abusing_kernel"],
            # legacy fields
            mem_slots=BinarySize.from_str(row["available_slots"]["mem"]) // mega,
            cpu_slots=row["available_slots"]["cpu"],
            gpu_slots=row["available_slots"].get("cuda.device", 0),
            tpu_slots=row["available_slots"].get("tpu.device", 0),
            used_mem_slots=BinarySize.from_str(row["occupied_slots"].get("mem", 0)) // mega,
            used_cpu_slots=float(row["occupied_slots"].get("cpu", 0)),
            used_gpu_slots=float(row["occupied_slots"].get("cuda.device", 0)),
            used_tpu_slots=float(row["occupied_slots"].get("tpu.device", 0)),
        )

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        rs = ctx.redis_stat
        live_stat = await redis_helper.execute(rs, lambda r: r.get(str(self.id)))
        if live_stat is not None:
            live_stat = msgpack.unpackb(live_stat)
        return live_stat

    async def resolve_cpu_cur_pct(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        rs = ctx.redis_stat
        live_stat = await redis_helper.execute(rs, lambda r: r.get(str(self.id)))
        if live_stat is not None:
            live_stat = msgpack.unpackb(live_stat)
            try:
                return float(live_stat["node"]["cpu_util"]["pct"])
            except (KeyError, TypeError, ValueError):
                return 0.0
        return 0.0

    async def resolve_mem_cur_bytes(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        rs = ctx.redis_stat
        live_stat = await redis_helper.execute(rs, lambda r: r.get(str(self.id)))
        if live_stat is not None:
            live_stat = msgpack.unpackb(live_stat)
            try:
                return int(live_stat["node"]["mem"]["current"])
            except (KeyError, TypeError, ValueError):
                return 0
        return 0

    async def resolve_hardware_metadata(
        self,
        info: graphene.ResolveInfo,
    ) -> Optional[Mapping[str, HardwareMetadata]]:
        if self.status != AgentStatus.ALIVE.name:
            return None
        graph_ctx: GraphQueryContext = info.context
        return await graph_ctx.registry.gather_agent_hwinfo(self.id)

    async def resolve_local_config(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        return {
            "agent": {
                "auto_terminate_abusing_kernel": self.auto_terminate_abusing_kernel,
            },
        }

    async def resolve_container_count(self, info: graphene.ResolveInfo) -> int:
        ctx: GraphQueryContext = info.context
        rs = ctx.redis_stat
        cnt = await redis_helper.execute(rs, lambda r: r.get(f"container_count.{self.id}"))
        return int(cnt) if cnt is not None else 0

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", None),
        "status": ("status", enum_field_getter(AgentStatus)),
        "status_changed": ("status_changed", dtparse),
        "region": ("region", None),
        "scaling_group": ("scaling_group", None),
        "schedulable": ("schedulabe", None),
        "addr": ("addr", None),
        "first_contact": ("first_contat", dtparse),
        "lost_at": ("lost_at", dtparse),
        "version": ("version", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("id", None),
        "status": ("status", None),
        "status_changed": ("status_changed", None),
        "region": ("region", None),
        "scaling_group": ("scaling_group", None),
        "schedulable": ("schedulable", None),
        "first_contact": ("first_contact", None),
        "lost_at": ("lost_at", None),
        "version": ("version", None),
        "available_slots": ("available_slots", None),
        "occupied_slots": ("occupied_slots", None),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        scaling_group: str = None,
        raw_status: Optional[str | AgentStatus] = None,
        filter: str = None,
    ) -> int:
        if isinstance(raw_status, str):
            status_list = [AgentStatus[s] for s in raw_status.split(",")]
        elif isinstance(raw_status, AgentStatus):
            status_list = [raw_status]
        query = sa.select([sa.func.count()]).select_from(agents)
        if scaling_group is not None:
            query = query.where(agents.c.scaling_group == scaling_group)
        if raw_status is not None:
            query = query.where(agents.c.status.in_(status_list))
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        scaling_group: str = None,
        raw_status: str = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[Agent]:
        if isinstance(raw_status, str):
            status_list = [AgentStatus[s] for s in raw_status.split(",")]
        elif isinstance(raw_status, AgentStatus):
            status_list = [raw_status]
        query = sa.select([agents]).select_from(agents).limit(limit).offset(offset)
        if scaling_group is not None:
            query = query.where(agents.c.scaling_group == scaling_group)
        if raw_status is not None:
            query = query.where(agents.c.status.in_(status_list))
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(
                agents.c.status.asc(),
                agents.c.scaling_group.asc(),
                agents.c.id.asc(),
            )
        async with graph_ctx.db.begin_readonly() as conn:
            return [cls.from_row(graph_ctx, row) async for row in (await conn.stream(query))]

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        scaling_group: str = None,
        raw_status: str = None,
    ) -> Sequence[Agent]:
        query = sa.select([agents]).select_from(agents)
        if scaling_group is not None:
            query = query.where(agents.c.scaling_group == scaling_group)
        if raw_status is not None:
            query = query.where(agents.c.status == AgentStatus[raw_status])
        async with graph_ctx.db.begin_readonly() as conn:
            return [cls.from_row(graph_ctx, row) async for row in (await conn.stream(query))]

    @classmethod
    async def batch_load(
        cls,
        graph_ctx: GraphQueryContext,
        agent_ids: Sequence[AgentId],
        *,
        raw_status: str = None,
    ) -> Sequence[Agent | None]:
        query = (
            sa.select([agents])
            .select_from(agents)
            .where(agents.c.id.in_(agent_ids))
            .order_by(
                agents.c.id,
            )
        )
        if raw_status is not None:
            query = query.where(agents.c.status == AgentStatus[raw_status])
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                agent_ids,
                lambda row: row["id"],
            )


class ModifyAgentInput(graphene.InputObjectType):
    schedulable = graphene.Boolean(required=False, default=True)
    scaling_group = graphene.String(required=False)


class AgentList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Agent, required=True)


async def _query_domain_groups_by_ak(
    db_conn: SAConnection,
    access_key: str,
    domain_name: str | None,
) -> tuple[str, list[uuid.UUID]]:
    kp_user_join = sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
    if domain_name is None:
        domain_query = (
            sa.select([users.c.uuid, users.c.domain_name])
            .select_from(kp_user_join)
            .where(keypairs.c.access_key == access_key)
        )
        row = (await db_conn.execute(domain_query)).first()
        user_domain = row.domain_name
        user_id = row.uuid
        group_join = association_groups_users
        group_cond = association_groups_users.c.user_id == user_id
    else:
        user_domain = domain_name
        group_join = kp_user_join.join(
            association_groups_users,
            association_groups_users.c.user_id == users.c.uuid,
        )
        group_cond = keypairs.c.access_key == access_key
    query = (
        sa.select([association_groups_users.c.group_id]).select_from(group_join).where(group_cond)
    )
    rows = (await db_conn.execute(query)).fetchall()
    group_ids = [row.group_id for row in rows]
    return user_domain, group_ids


async def _append_sgroup_from_clause(
    graph_ctx: GraphQueryContext,
    query: sa.sql.Select,
    access_key: str,
    domain_name: str | None,
    scaling_group: str | None = None,
) -> sa.sql.Select:
    if scaling_group is not None:
        query = query.where(agents.c.scaling_group == scaling_group)
    else:
        async with graph_ctx.db.begin_readonly() as conn:
            domain_name, group_ids = await _query_domain_groups_by_ak(conn, access_key, domain_name)
            sgroups = await query_allowed_sgroups(conn, domain_name, group_ids, access_key)
            names = [sgroup["name"] for sgroup in sgroups]
        query = query.where(agents.c.scaling_group.in_(names))
    return query


class AgentSummary(graphene.ObjectType):
    """
    A schema for normal users.
    """

    class Meta:
        interfaces = (Item,)

    status = graphene.String()
    scaling_group = graphene.String()
    schedulable = graphene.Boolean()
    available_slots = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    architecture = graphene.String()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> Agent:
        return cls(
            id=row["id"],
            status=row["status"].name,
            scaling_group=row["scaling_group"],
            schedulable=row["schedulable"],
            available_slots=row["available_slots"].to_json(),
            occupied_slots=row["occupied_slots"].to_json(),
            architecture=row["architecture"],
        )

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", None),
        "status": ("status", enum_field_getter(AgentStatus)),
        "scaling_group": ("scaling_group", None),
        "schedulable": ("schedulabe", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("id", None),
        "status": ("status", None),
        "scaling_group": ("scaling_group", None),
        "schedulable": ("schedulable", None),
        "available_slots": ("available_slots", None),
        "occupied_slots": ("occupied_slots", None),
    }

    @classmethod
    async def batch_load(
        cls,
        graph_ctx: GraphQueryContext,
        agent_ids: Sequence[AgentId],
        *,
        domain_name: str | None,
        raw_status: str = None,
        scaling_group: str = None,
        access_key: str,
    ) -> Sequence[Agent | None]:
        query = (
            sa.select([agents])
            .select_from(agents)
            .where(agents.c.id.in_(agent_ids))
            .order_by(
                agents.c.id,
            )
        )
        if raw_status is not None:
            query = query.where(agents.c.status == AgentStatus[raw_status])
        query = await _append_sgroup_from_clause(
            graph_ctx, query, access_key, domain_name, scaling_group
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                agent_ids,
                lambda row: row["id"],
            )

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        access_key: str,
        domain_name: str | None = None,
        scaling_group: str | None = None,
        raw_status: str = None,
        filter: str = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(agents)
        query = await _append_sgroup_from_clause(
            graph_ctx, query, access_key, domain_name, scaling_group
        )

        if raw_status is not None:
            query = query.where(agents.c.status == AgentStatus[raw_status])
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        access_key: str,
        domain_name: str | None = None,
        scaling_group: str | None = None,
        raw_status: str = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[Agent]:
        query = sa.select([agents]).select_from(agents).limit(limit).offset(offset)
        query = await _append_sgroup_from_clause(
            graph_ctx, query, access_key, domain_name, scaling_group
        )

        if raw_status is not None:
            query = query.where(agents.c.status == AgentStatus[raw_status])
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(
                agents.c.status.asc(),
                agents.c.scaling_group.asc(),
                agents.c.id.asc(),
            )
        async with graph_ctx.db.begin_readonly() as conn:
            return [cls.from_row(graph_ctx, row) async for row in (await conn.stream(query))]


class AgentSummaryList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(AgentSummary, required=True)


async def recalc_agent_resource_occupancy(db_conn: SAConnection, agent_id: AgentId) -> None:
    query = (
        sa.select([
            kernels.c.occupied_slots,
        ])
        .select_from(kernels)
        .where(
            (kernels.c.agent == agent_id)
            & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
        )
    )
    occupied_slots = ResourceSlot()
    result = await db_conn.execute(query)
    for row in result:
        occupied_slots += row["occupied_slots"]
    query = (
        sa.update(agents)
        .values({
            "occupied_slots": occupied_slots,
        })
        .where(agents.c.id == agent_id)
    )
    await db_conn.execute(query)


async def recalc_agent_resource_occupancy_using_orm(
    db_session: SASession, agent_id: AgentId
) -> None:
    agent_query = (
        sa.select(AgentRow)
        .where(AgentRow.id == agent_id)
        .options(
            selectinload(AgentRow.kernels),
            with_loader_criteria(
                KernelRow, KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)
            ),
        )
    )
    occupied_slots = ResourceSlot()
    agent_row = cast(AgentRow, await db_session.scalar(agent_query))
    kernel_rows = cast(list[KernelRow], agent_row.kernels)
    for kernel in kernel_rows:
        if kernel.status in AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES:
            occupied_slots += kernel.occupied_slots
    agent_row.occupied_slots = occupied_slots


class ModifyAgent(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        id = graphene.String(required=True)
        props = ModifyAgentInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        props: ModifyAgentInput,
    ) -> ModifyAgent:
        graph_ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, "schedulable")
        set_if_set(props, data, "scaling_group")
        # TODO: Need to skip the following RPC call if the agent is not alive, or timeout.
        if (scaling_group := data.get("scaling_group")) is not None:
            await graph_ctx.registry.update_scaling_group(id, scaling_group)

        update_query = sa.update(agents).values(data).where(agents.c.id == id)
        return await simple_db_mutate(cls, graph_ctx, update_query)

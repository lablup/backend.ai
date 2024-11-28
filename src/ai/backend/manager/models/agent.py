from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Mapping,
    Optional,
    Self,
    Sequence,
    TypeAlias,
    cast,
    override,
)

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from redis.asyncio import Redis
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, relationship, selectinload, with_loader_criteria
from sqlalchemy.sql.expression import false, true

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import AccessKey, AgentId, BinarySize, HardwareMetadata, ResourceSlot

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
from .kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    ComputeContainer,
    KernelRow,
    KernelStatus,
)
from .keypair import KeyPairRow, keypairs
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import AgentPermission, ScalingGroupPermission
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

    compute_containers = graphene.List(ComputeContainer, status=graphene.String())

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

    async def resolve_compute_containers(
        self, info: graphene.ResolveInfo, *, status: Optional[str] = None
    ) -> list[ComputeContainer]:
        ctx: GraphQueryContext = info.context
        _status = KernelStatus[status] if status is not None else None
        loader = ctx.dataloader_manager.get_loader(
            ctx,
            "ComputeContainer.by_agent_id",
            status=_status,
        )
        return await loader.load(self.id)

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "Agent.live_stat")
        return await loader.load(self.id)

    async def resolve_cpu_cur_pct(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "Agent.cpu_cur_pct")
        return await loader.load(self.id)

    async def resolve_mem_cur_bytes(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "Agent.mem_cur_bytes")
        return await loader.load(self.id)

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
        loader = ctx.dataloader_manager.get_loader(ctx, "Agent.container_count")
        return await loader.load(self.id)

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", None),
        "status": ("status", enum_field_getter(AgentStatus)),
        "status_changed": ("status_changed", dtparse),
        "region": ("region", None),
        "scaling_group": ("scaling_group", None),
        "schedulable": ("schedulable", None),
        "addr": ("addr", None),
        "first_contact": ("first_contact", dtparse),
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
        scaling_group: Optional[str] = None,
        raw_status: Optional[str | AgentStatus] = None,
        filter: Optional[str] = None,
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
        scaling_group: Optional[str] = None,
        raw_status: Optional[str] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
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
        scaling_group: Optional[str] = None,
        raw_status: Optional[str] = None,
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
        raw_status: Optional[str] = None,
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

    @classmethod
    async def batch_load_live_stat(
        cls, ctx: GraphQueryContext, agent_ids: Sequence[str]
    ) -> Sequence[Any]:
        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            for agent_id in agent_ids:
                await pipe.get(agent_id)
            return pipe

        ret = []
        for stat in await redis_helper.execute(ctx.redis_stat, _pipe_builder):
            if stat is not None:
                ret.append(msgpack.unpackb(stat))
            else:
                ret.append(None)

        return ret

    @classmethod
    async def batch_load_cpu_cur_pct(
        cls, ctx: GraphQueryContext, agent_ids: Sequence[str]
    ) -> Sequence[Any]:
        ret = []
        for stat in await cls.batch_load_live_stat(ctx, agent_ids):
            if stat is not None:
                try:
                    ret.append(float(stat["node"]["cpu_util"]["pct"]))
                except (KeyError, TypeError, ValueError):
                    ret.append(0.0)
            else:
                ret.append(0.0)
        return ret

    @classmethod
    async def batch_load_mem_cur_bytes(
        cls, ctx: GraphQueryContext, agent_ids: Sequence[str]
    ) -> Sequence[Any]:
        ret = []
        for stat in await cls.batch_load_live_stat(ctx, agent_ids):
            if stat is not None:
                try:
                    ret.append(float(stat["node"]["mem"]["current"]))
                except (KeyError, TypeError, ValueError):
                    ret.append(0)
            else:
                ret.append(0)
        return ret

    @classmethod
    async def batch_load_container_count(
        cls, ctx: GraphQueryContext, agent_ids: Sequence[str]
    ) -> Sequence[int]:
        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            for agent_id in agent_ids:
                await pipe.get(f"container_count.{agent_id}")
            return pipe

        ret = []
        for cnt in await redis_helper.execute(ctx.redis_stat, _pipe_builder):
            ret.append(int(cnt) if cnt is not None else 0)
        return ret


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
    from .scaling_group import query_allowed_sgroups

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
    ) -> Self:
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
        "schedulable": ("schedulable", None),
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
        access_key: AccessKey,
        domain_name: str | None,
        raw_status: Optional[str] = None,
        scaling_group: Optional[str] = None,
    ) -> Sequence[Optional[Self]]:
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
        raw_status: Optional[str] = None,
        filter: Optional[str] = None,
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
        raw_status: Optional[str] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[Self]:
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


async def recalc_agent_resource_occupancy(db_session: SASession, agent_id: AgentId) -> None:
    _stmt = (
        sa.select(KernelRow)
        .where(
            (KernelRow.agent == agent_id)
            & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        .options(load_only(KernelRow.occupied_slots))
    )
    kernel_rows = cast(list[KernelRow], (await db_session.scalars(_stmt)).all())
    occupied_slots = ResourceSlot()
    for row in kernel_rows:
        occupied_slots += row.occupied_slots

    _update_stmt = (
        sa.update(AgentRow).values(occupied_slots=occupied_slots).where(AgentRow.id == agent_id)
    )
    await db_session.execute(_update_stmt)


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


WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)
# TypeAlias is deprecated since 3.12 but mypy does not follow up yet

OWNER_PERMISSIONS: frozenset[AgentPermission] = frozenset([perm for perm in AgentPermission])
ADMIN_PERMISSIONS: frozenset[AgentPermission] = frozenset([perm for perm in AgentPermission])
MONITOR_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.READ_ATTRIBUTE,
    AgentPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.CREATE_COMPUTE_SESSION,
    AgentPermission.CREATE_SERVICE,
])
MEMBER_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.CREATE_COMPUTE_SESSION,
    AgentPermission.CREATE_SERVICE,
])


@dataclass
class AgentPermissionContext(AbstractPermissionContext[AgentPermission, AgentRow, AgentId]):
    from .scaling_group import ScalingGroupPermissionContext

    sgroup_permission_ctx: Optional[ScalingGroupPermissionContext] = None

    @property
    def query_condition(self) -> Optional[WhereClauseType]:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: Optional[WhereClauseType],
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, AgentRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, AgentRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )

        if self.sgroup_permission_ctx is not None:
            if cond is not None:
                sgroup_names = self.sgroup_permission_ctx.sgroup_to_permissions_map.keys()
                cond = cond & AgentRow.scaling_group.in_(sgroup_names)
        return cond

    def apply_sgroup_permission_ctx(
        self, sgroup_permission_ctx: ScalingGroupPermissionContext
    ) -> None:
        self.sgroup_permission_ctx = sgroup_permission_ctx

    async def build_query(self) -> Optional[sa.sql.Select]:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(AgentRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: AgentRow) -> frozenset[AgentPermission]:
        agent_row = rbac_obj
        agent_id = cast(AgentId, agent_row.id)
        permissions: set[AgentPermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(agent_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(agent_id, set())

        if self.sgroup_permission_ctx is not None:
            sgroup_permission_map = self.sgroup_permission_ctx.sgroup_to_permissions_map
            sgroup_perms = sgroup_permission_map.get(agent_row.scaling_group)
            if sgroup_perms is None or ScalingGroupPermission.AGENT_PERMISSIONS not in sgroup_perms:
                permissions = set()

        return frozenset(permissions)


class AgentPermissionContextBuilder(
    AbstractPermissionContextBuilder[AgentPermission, AgentPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[AgentPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> AgentPermissionContext:
        from .domain import DomainRow

        perm_ctx = AgentPermissionContext()
        _domain_query_stmt = sa.select(DomainRow).options(load_only(DomainRow.name))
        for row in await self.db_session.scalars(_domain_query_stmt):
            to_be_merged = await self.build_ctx_in_domain_scope(ctx, DomainScope(row.name))
            perm_ctx.merge(to_be_merged)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForDomainRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _stmt = (
            sa.select(ScalingGroupForDomainRow)
            .where(ScalingGroupForDomainRow.domain == scope.domain_name)
            .options(
                joinedload(ScalingGroupForDomainRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForProjectRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _stmt = (
            sa.select(ScalingGroupForProjectRow)
            .where(ScalingGroupForProjectRow.group == scope.project_id)
            .options(
                joinedload(ScalingGroupForProjectRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForKeypairsRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _kp_stmt = (
            sa.select(KeyPairRow)
            .where(KeyPairRow.user == scope.user_id)
            .options(load_only(KeyPairRow.access_key))
        )
        kp_rows = (await self.db_session.scalars(_kp_stmt)).all()
        access_keys = cast(list[AccessKey], [r.access_key for r in kp_rows])

        _stmt = (
            sa.select(ScalingGroupForKeypairsRow)
            .where(ScalingGroupForKeypairsRow.access_key.in_(access_keys))
            .options(
                joinedload(ScalingGroupForKeypairsRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[AgentPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[AgentPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[AgentPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[AgentPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[AgentPermission]:
        return MEMBER_PERMISSIONS


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: ScopeType,
    requested_permission: AgentPermission,
) -> AgentPermissionContext:
    from .scaling_group import ScalingGroupPermissionContextBuilder

    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        sgroup_perm_ctx = await ScalingGroupPermissionContextBuilder(db_session).build(
            ctx, target_scope, ScalingGroupPermission.AGENT_PERMISSIONS
        )

        builder = AgentPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
        permission_ctx.apply_sgroup_permission_ctx(sgroup_perm_ctx)
    return permission_ctx

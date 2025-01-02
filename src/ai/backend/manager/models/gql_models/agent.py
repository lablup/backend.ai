from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
)

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from redis.asyncio import Redis
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    HardwareMetadata,
)

from ..agent import (
    AgentRow,
    AgentStatus,
    agents,
    get_permission_ctx,
)
from ..base import (
    FilterExprArg,
    Item,
    OrderExprArg,
    PaginatedConnectionField,
    PaginatedList,
    batch_result,
    generate_sql_info_for_gql_connection,
    privileged_mutation,
    set_if_set,
    simple_db_mutate,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..group import AssocGroupUserRow
from ..kernel import ComputeContainer, KernelStatus
from ..keypair import keypairs
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from ..rbac import (
    ScopeType,
)
from ..rbac.context import ClientContext
from ..rbac.permission_defs import AgentPermission
from ..user import UserRole, users
from .fields import AgentPermissionField
from .kernel import KernelConnection, KernelNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

__all__ = (
    "Agent",
    "AgentNode",
    "AgentConnection",
)

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


class AgentNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.12.0."

    row_id = graphene.String()
    status = graphene.String()
    status_changed = GQLDateTime()
    region = graphene.String()
    scaling_group = graphene.String()
    schedulable = graphene.Boolean()
    available_slots = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    addr = graphene.String(description="Agent's address with port. (bind/advertised host:port)")
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

    kernel_nodes = PaginatedConnectionField(
        KernelConnection,
    )

    permissions = graphene.List(
        AgentPermissionField,
        description=f"Added in 24.12.0. One of {[val.value for val in AgentPermission]}.",
    )

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: AgentRow,
    ) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            status=row.status.name,
            status_changed=row.status_changed,
            region=row.region,
            scaling_group=row.scaling_group,
            schedulable=row.schedulable,
            available_slots=row.available_slots,
            occupied_slots=row.occupied_slots,
            addr=row.addr,
            architecture=row.architecture,
            first_contact=row.first_contact,
            lost_at=row.lost_at,
            version=row.version,
            compute_plugins=row.compute_plugins,
            auto_terminate_abusing_kernel=row.auto_terminate_abusing_kernel,
        )

    @classmethod
    def parse(
        cls,
        info: graphene.ResolveInfo,
        row: AgentRow,
        permissions: Iterable[AgentPermission],
    ) -> Self:
        result = cls.from_row(info.context, row)
        result.permissions = list(permissions)
        return result

    async def resolve_kernel_nodes(
        self, info: graphene.ResolveInfo
    ) -> ConnectionResolverResult[KernelNode]:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, KernelNode.batch_load_by_agent_id)
        result = await loader.load(self.id)
        return ConnectionResolverResult(result, None, None, None, len(result))

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, self.batch_load_live_stat)
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
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, self.batch_load_container_count)
        return await loader.load(self.id)

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

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        scope: ScopeType,
        permission: AgentPermission,
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(_queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(_queryorder_colmap))
            if order_expr is not None
            else None
        )
        (
            query,
            cnt_query,
            _,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            AgentRow,
            AgentRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond)
            cnt_query = cnt_query.where(cond)
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                agent_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
        result: list[AgentNode] = [
            cls.parse(info, row, await permission_ctx.calculate_final_permission(row))
            for row in agent_rows
        ]

        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class AgentConnection(Connection):
    class Meta:
        node = AgentNode
        description = "Added in 24.12.0."


### Legacy


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
        loader = ctx.dataloader_manager.get_loader_by_func(
            ctx,
            ComputeContainer.batch_load_by_agent_id,
            status=_status,
        )
        return await loader.load(self.id)

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, Agent.batch_load_live_stat)
        return await loader.load(self.id)

    async def resolve_cpu_cur_pct(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, Agent.batch_load_cpu_cur_pct)
        return await loader.load(self.id)

    async def resolve_mem_cur_bytes(self, info: graphene.ResolveInfo) -> Any:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, Agent.batch_load_mem_cur_bytes)
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
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, Agent.batch_load_container_count)
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
        group_join = AssocGroupUserRow
        group_cond = AssocGroupUserRow.user_id == user_id
    else:
        user_domain = domain_name
        group_join = kp_user_join.join(
            AssocGroupUserRow,
            AssocGroupUserRow.user_id == users.c.uuid,
        )
        group_cond = keypairs.c.access_key == access_key
    query = sa.select(AssocGroupUserRow.group_id).select_from(group_join).where(group_cond)
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
    from ..scaling_group import query_allowed_sgroups

    if scaling_group is not None:
        query = query.where(agents.c.scaling_group == scaling_group)
    else:
        async with graph_ctx.db.begin_readonly() as conn:
            domain_name, group_ids = await _query_domain_groups_by_ak(conn, access_key, domain_name)
            sgroups = await query_allowed_sgroups(conn, domain_name, group_ids, access_key)
            names = [sgroup["name"] for sgroup in sgroups]
        query = query.where(agents.c.scaling_group.in_(names))
    return query


class AgentList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Agent, required=True)


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
        domain_name: Optional[str] = None,
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


class ModifyAgentInput(graphene.InputObjectType):
    schedulable = graphene.Boolean(required=False, default=True)
    scaling_group = graphene.String(required=False)


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
        data: dict[str, Any] = {}
        set_if_set(props, data, "schedulable")
        set_if_set(props, data, "scaling_group")
        # TODO: Need to skip the following RPC call if the agent is not alive, or timeout.
        if (scaling_group := data.get("scaling_group")) is not None:
            await graph_ctx.registry.update_scaling_group(id, scaling_group)

        update_query = sa.update(agents).values(data).where(agents.c.id == id)
        return await simple_db_mutate(cls, graph_ctx, update_query)

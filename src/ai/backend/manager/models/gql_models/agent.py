from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
)

import graphene
import graphql
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from redis.asyncio import Redis

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import (
    HardwareMetadata,
)

from ..agent import (
    AgentRow,
    AgentStatus,
    get_permission_ctx,
)
from ..base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from ..rbac import (
    ScopeType,
)
from ..rbac.context import ClientContext
from ..rbac.permission_defs import AgentPermission

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


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


class AgentPermissionValueField(graphene.Scalar):
    class Meta:
        description = f"Added in 24.09.0. One of {[val.value for val in AgentPermission]}."

    @staticmethod
    def serialize(val: AgentPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return AgentPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> AgentPermission:
        return AgentPermission(value)


class AgentNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.09.0."

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

    permissions = graphene.List(
        AgentPermissionValueField,
        description=f"Added in 24.09.0. One of {[val.value for val in AgentPermission]}.",
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
        description = "Added in 24.09.0."

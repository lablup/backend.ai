from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
    cast,
)

import graphene
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.orm import selectinload

from ai.backend.common.types import ClusterMode, SessionId, SessionResult
from ai.backend.manager.idle import ReportInfo

from ..base import (
    BigInt,
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
    set_if_set,
)
from ..gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
    GlobalIDField,
    ResolvedGlobalID,
)
from ..minilang import ArrayFieldItem, JSONFieldItem
from ..minilang.ordering import ColumnMapType, QueryOrderParser
from ..minilang.queryfilter import FieldSpecType, QueryFilterParser, enum_field_getter
from ..rbac import ProjectScope
from ..rbac.context import ClientContext
from ..rbac.permission_defs import ComputeSessionPermission
from ..session import SessionRow, SessionStatus, SessionTypes, get_permission_ctx
from ..user import UserRole
from .kernel import KernelConnection

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


_queryfilter_fieldspec: FieldSpecType = {
    "id": ("id", None),
    "type": ("session_type", enum_field_getter(SessionTypes)),
    "name": ("name", None),
    "priority": ("priority", None),
    "agent_ids": (ArrayFieldItem("agent_ids"), None),
    "domain_name": ("domain_name", None),
    "project_id": ("project_id", None),
    "user_id": ("user_uuid", None),
    "access_key": ("access_key", None),
    "scaling_group": ("scaling_group_name", None),
    "cluster_mode": ("cluster_mode", lambda s: ClusterMode[s]),
    "cluster_size": ("cluster_size", None),
    "status": ("status", enum_field_getter(SessionStatus)),
    "status_info": ("status_info", None),
    "result": ("result", enum_field_getter(SessionResult)),
    "created_at": ("created_at", dtparse),
    "terminated_at": ("terminated_at", dtparse),
    "starts_at": ("starts_at", dtparse),
    "scheduled_at": (
        JSONFieldItem("status_history", SessionStatus.SCHEDULED.name),
        dtparse,
    ),
    "startup_command": ("startup_command", None),
}

_queryorder_colmap: ColumnMapType = {
    "id": ("id", None),
    "type": ("session_type", None),
    "name": ("name", None),
    "priority": ("priority", None),
    "image": ("images", None),
    "agent_ids": ("agent_ids", None),
    "domain_name": ("domain_name", None),
    "project_id": ("project_id", None),
    "user_id": ("user_uuid", None),
    "access_key": ("access_key", None),
    "scaling_group": ("scaling_group_name", None),
    "cluster_mode": ("cluster_mode", None),
    "cluster_size": ("cluster_size", None),
    "status": ("status", None),
    "status_info": ("status_info", None),
    "result": ("result", None),
    "created_at": ("created_at", None),
    "terminated_at": ("terminated_at", None),
    "starts_at": ("starts_at", None),
    "scheduled_at": (
        JSONFieldItem("status_history", SessionStatus.SCHEDULED.name),
        None,
    ),
}


class SessionPermissionValueField(graphene.Scalar):
    class Meta:
        description = f"Added in 24.09.0. One of {[val.value for val in ComputeSessionPermission]}."

    @staticmethod
    def serialize(val: ComputeSessionPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ComputeSessionPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> ComputeSessionPermission:
        return ComputeSessionPermission(value)


class ComputeSessionNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.09.0."

    # identity
    row_id = graphene.UUID(description="ID of session.")
    tag = graphene.String()
    name = graphene.String()
    type = graphene.String()
    priority = graphene.Int()

    # cluster
    cluster_template = graphene.String()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()

    # ownership
    domain_name = graphene.String()
    project_id = graphene.UUID()
    user_id = graphene.UUID()
    access_key = graphene.String()
    permissions = graphene.List(
        SessionPermissionValueField,
        description=f"One of {[val.value for val in ComputeSessionPermission]}.",
    )

    # status
    status = graphene.String()
    # status_changed = GQLDateTime()  # FIXME: generated attribute
    status_info = graphene.String()
    status_data = graphene.JSONString()
    status_history = graphene.JSONString()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    starts_at = GQLDateTime()
    scheduled_at = GQLDateTime()

    startup_command = graphene.String()
    result = graphene.String()
    commit_status = graphene.String()
    abusing_reports = graphene.List(lambda: graphene.JSONString)
    idle_checks = graphene.JSONString()

    # resources
    agent_ids = graphene.List(lambda: graphene.String)
    resource_opts = graphene.JSONString()
    scaling_group = graphene.String()
    service_ports = graphene.JSONString()
    vfolder_mounts = graphene.List(lambda: graphene.String)
    occupied_slots = graphene.JSONString()
    requested_slots = graphene.JSONString()

    # statistics
    num_queries = BigInt()
    inference_metrics = graphene.JSONString()

    # relations
    kernel_nodes = PaginatedConnectionField(
        KernelConnection,
    )
    # dependencies = PaginatedConnectionField(ComputeSessionConnection,)

    async def resolve_idle_checks(self, info: graphene.ResolveInfo) -> dict[str, Any] | None:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, self.batch_load_idle_checks
        )
        return await loader.load(self.row_id)

    @classmethod
    async def batch_load_idle_checks(
        cls, ctx: GraphQueryContext, session_ids: Sequence[SessionId]
    ) -> list[dict[str, ReportInfo]]:
        check_result = await ctx.idle_checker_host.get_batch_idle_check_report(session_ids)
        return [check_result[sid] for sid in session_ids]

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: SessionRow,
        *,
        permissions: Optional[Iterable[ComputeSessionPermission]] = None,
    ) -> Self:
        status_history = row.status_history or {}
        raw_scheduled_at = status_history.get(SessionStatus.SCHEDULED.name)
        result = cls(
            # identity
            id=row.id,  # auto-converted to Relay global ID
            row_id=row.id,
            tag=row.tag,
            name=row.name,
            type=row.session_type,
            cluster_template=None,
            cluster_mode=row.cluster_mode,
            cluster_size=row.cluster_size,
            priority=row.priority,
            # ownership
            domain_name=row.domain_name,
            project_id=row.group_id,
            user_id=row.user_uuid,
            access_key=row.access_key,
            # status
            status=row.status.name,
            # status_changed=row.status_changed,  # FIXME: generated attribute
            status_info=row.status_info,
            status_data=row.status_data,
            status_history=status_history,
            created_at=row.created_at,
            starts_at=row.starts_at,
            terminated_at=row.terminated_at,
            scheduled_at=datetime.fromisoformat(raw_scheduled_at)
            if raw_scheduled_at is not None
            else None,
            startup_command=row.startup_command,
            result=row.result.name,
            # resources
            agent_ids=row.agent_ids,
            scaling_group=row.scaling_group_name,
            vfolder_mounts=row.vfolder_mounts,
            occupied_slots=row.occupying_slots.to_json(),
            requested_slots=row.requested_slots.to_json(),
            # statistics
            num_queries=row.num_queries,
        )
        result.permissions = [] if permissions is None else permissions
        return result

    async def resolve_kernel_nodes(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "KernelNode.by_session_id")
        kernels = await loader.load(self.row_id)
        return ConnectionResolverResult(
            kernels,
            None,
            None,
            None,
            total_count=len(kernels),
        )

    @classmethod
    async def get_accessible_node(
        cls,
        info: graphene.ResolveInfo,
        id: ResolvedGlobalID,
        project_id: uuid.UUID,
        permission: ComputeSessionPermission,
    ) -> Self | None:
        graph_ctx: GraphQueryContext = info.context
        user = graph_ctx.user
        client_ctx = ClientContext(graph_ctx.db, user["domain_name"], user["uuid"], user["role"])
        _, session_id = id
        async with graph_ctx.db.connect() as db_conn:
            permission_ctx = await get_permission_ctx(
                db_conn, client_ctx, ProjectScope(project_id), permission
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return None
            query = (
                sa.select(SessionRow)
                .where(cond & (SessionRow.id == uuid.UUID(session_id)))
                .options(selectinload(SessionRow.kernels))
            )
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                session_row = await db_session.scalar(query)
        result = cls.from_row(
            graph_ctx,
            session_row,
            permissions=await permission_ctx.calculate_final_permission(session_row),
        )
        return result

    @classmethod
    async def get_accessible_connection(
        cls,
        info: graphene.ResolveInfo,
        project_id: uuid.UUID,
        permission: ComputeSessionPermission,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
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
            SessionRow,
            SessionRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        query = query.options(selectinload(SessionRow.kernels))
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(
                db_conn, client_ctx, ProjectScope(project_id), permission
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond)
            cnt_query = cnt_query.where(cond)
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                session_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
        result: list[ComputeSessionNode] = [
            cls.from_row(
                graph_ctx,
                row,
                permissions=await permission_ctx.calculate_final_permission(row),
            )
            for row in session_rows
        ]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class ComputeSessionConnection(Connection):
    class Meta:
        node = ComputeSessionNode
        description = "Added in 24.09.0."


class ModifyComputeSession(graphene.relay.ClientIDMutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)  # TODO: check if working

    class Input:
        id = GlobalIDField(required=True)
        name = graphene.String(required=False)
        priority = graphene.Int(required=False)
        client_mutation_id = graphene.String(required=False)  # automatic input from relay

    # Output fields
    item = graphene.Field(ComputeSessionNode)
    client_mutation_id = graphene.String()  # Relay output

    @classmethod
    async def mutate_and_get_payload(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        **input,
    ) -> ModifyComputeSession:
        graph_ctx: GraphQueryContext = info.context
        _, raw_session_id = cast(ResolvedGlobalID, input["id"])
        session_id = SessionId(uuid.UUID(raw_session_id))
        async with graph_ctx.db.begin_session() as db_sess:
            data: dict[str, Any] = {}
            set_if_set(input, data, "name")
            set_if_set(input, data, "priority")
            query = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(data)
                .returning(SessionRow)
            )
            result = await db_sess.execute(query)
            session_row = result.fetchone()
        return ModifyComputeSession(
            ComputeSessionNode.from_row(graph_ctx, session_row),
            input.get("client_mutation_id"),
        )

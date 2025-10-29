from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    Optional,
    Self,
    cast,
)

import graphene
import graphql
import more_itertools
import sqlalchemy as sa
import trafaret as t
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common import validators as tx
from ai.backend.common.defs.session import SESSION_PRIORITY_MAX, SESSION_PRIORITY_MIN
from ai.backend.common.exception import SessionWithInvalidStateError
from ai.backend.common.types import (
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    VFolderMount,
)
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.idle import ReportInfo
from ai.backend.manager.models.gql_models.user import UserNode
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import agg_to_array
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
)
from ai.backend.manager.services.session.actions.modify_session import (
    ModifySessionAction,
    SessionModifier,
)
from ai.backend.manager.types import OptionalState

from ..base import (
    BigInt,
    FilterExprArg,
    Item,
    OrderExprArg,
    PaginatedConnectionField,
    PaginatedList,
    batch_multiresult_in_session,
    batch_result_in_session,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
    GlobalIDField,
    ResolvedGlobalID,
)
from ..minilang import ArrayFieldItem, JSONFieldItem, ORMFieldItem
from ..minilang.ordering import ColumnMapType, QueryOrderParser
from ..minilang.queryfilter import FieldSpecType, QueryFilterParser
from ..rbac import ScopeType, SystemScope
from ..rbac.context import ClientContext
from ..rbac.permission_defs import ComputeSessionPermission
from ..rbac.permission_defs import VFolderPermission as VFolderRBACPermission
from ..session import (
    DEFAULT_SESSION_ORDERING,
    SessionDependencyRow,
    SessionRow,
    SessionTypes,
    by_domain_name,
    by_raw_filter,
    by_resource_group_name,
    by_status,
    get_permission_ctx,
)
from ..types import (
    QueryCondition,
    QueryOption,
    join_by_related_field,
    load_related_field,
)
from ..user import UserRole, UserRow
from ..vfolder import VFolderRow
from ..vfolder import get_permission_ctx as get_vfolder_permission_ctx
from .group import GroupRow
from .kernel import ComputeContainer, KernelConnection, KernelNode
from .vfolder import VirtualFolderConnection, VirtualFolderNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

__all__ = (
    "ComputeSessionNode",
    "ComputeSessionConnection",
    "ModifyComputeSession",
    "ModifyComputeSession",
    "ComputeSession",
    "ComputeSessionList",
    "InferenceSession",
    "InferenceSessionList",
)


_queryfilter_fieldspec: FieldSpecType = {
    "id": ("id", None),
    "type": ("session_type", lambda s: SessionTypes(s)),
    "name": ("name", None),
    "priority": ("priority", None),
    "images": (ArrayFieldItem("images"), None),
    "image": (ArrayFieldItem("images"), None),
    "agent_ids": (ArrayFieldItem("agent_ids"), None),
    "domain_name": ("domain_name", None),
    "project_id": ("group_id", None),
    "user_id": ("user_uuid", None),
    "full_name": (ORMFieldItem(UserRow.full_name), None),
    "group_name": (ORMFieldItem(GroupRow.name), None),
    "user_email": (ORMFieldItem(UserRow.email), None),
    "access_key": ("access_key", None),
    "scaling_group": ("scaling_group_name", None),
    "cluster_mode": ("cluster_mode", lambda s: ClusterMode(s)),
    "cluster_size": ("cluster_size", None),
    "status": ("status", lambda s: SessionStatus(s)),
    "status_info": ("status_info", None),
    "result": ("result", lambda s: SessionResult(s)),
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
    "images": ("images", None),
    "image": ("images", None),
    "agent_ids": ("agent_ids", None),
    "domain_name": ("domain_name", None),
    "project_id": ("group_id", None),
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
    priority = graphene.Int(
        description="Added in 24.09.0.",
    )

    # cluster
    cluster_template = graphene.String()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()

    # ownership
    domain_name = graphene.String()
    project_id = graphene.UUID()
    user_id = graphene.UUID()
    owner = graphene.Field(UserNode, description="Added in 25.13.0.")
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

    queue_position = graphene.Int(description="Added in 25.13.0.")

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
    image_references = graphene.List(
        lambda: graphene.String,
        description="Added in 25.4.0.",
    )
    vfolder_nodes = PaginatedConnectionField(
        VirtualFolderConnection,
        description="Added in 25.4.0.",
    )

    # statistics
    num_queries = BigInt()
    inference_metrics = graphene.JSONString()

    # relations
    kernel_nodes = PaginatedConnectionField(
        KernelConnection,
    )
    dependents = PaginatedConnectionField(
        "ai.backend.manager.models.gql_models.session.ComputeSessionConnection",
        description="Added in 24.09.0.",
    )
    dependees = PaginatedConnectionField(
        "ai.backend.manager.models.gql_models.session.ComputeSessionConnection",
        description="Added in 24.09.0.",
    )
    graph = PaginatedConnectionField(
        "ai.backend.manager.models.gql_models.session.ComputeSessionConnection",
        description="Added in 24.09.0.",
    )

    @classmethod
    async def get_node(
        cls,
        info: graphene.ResolveInfo,
        id: str,
    ) -> Optional[Self]:
        graphene_ctx: GraphQueryContext = info.context
        _, raw_session_id = AsyncNode.resolve_global_id(info, id)
        async with graphene_ctx.db.begin_readonly_session() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == uuid.UUID(raw_session_id))
                .options(selectinload(SessionRow.kernels), joinedload(SessionRow.user))
            )
            query_result = await db_session.scalar(stmt)
            return cls.from_row(graphene_ctx, query_result) if query_result is not None else None

    @classmethod
    def _add_basic_options_to_query(
        cls, stmt: sa.sql.Select, is_count: bool = False
    ) -> sa.sql.Select:
        options = [
            join_by_related_field(SessionRow.user),
            join_by_related_field(SessionRow.group),
        ]
        if not is_count:
            options = [
                *options,
                load_related_field(SessionRow.kernel_load_option()),
                load_related_field(SessionRow.user_load_option(already_joined=True)),
                load_related_field(SessionRow.project_load_option(already_joined=True)),
            ]
        for option in options:
            stmt = option(stmt)
        return stmt

    async def resolve_queue_position(self, info: graphene.ResolveInfo) -> Optional[int]:
        if self.status != SessionStatus.PENDING:
            return None
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, self._batch_load_queue_position
        )
        return await loader.load(self.row_id)

    async def _batch_load_queue_position(
        self, ctx: GraphQueryContext, session_ids: Sequence[SessionId]
    ) -> list[Optional[int]]:
        positions = await ctx.valkey_schedule.get_queue_positions(session_ids)
        return positions

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
            owner=UserNode.from_row(ctx, row.user),
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
            # TODO: Deprecate 'vfolder_mounts' and replace it with a list of VirtualFolderNodes
            vfolder_mounts=[vf.vfid.folder_id for vf in row.vfolders_sorted_by_id],
            occupied_slots=row.occupying_slots.to_json(),
            requested_slots=row.requested_slots.to_json(),
            image_references=row.images,
            service_ports=row.main_kernel.service_ports,
            # statistics
            num_queries=row.num_queries,
        )
        result.permissions = [] if permissions is None else permissions
        return result

    @classmethod
    def from_dataclass(
        cls,
        ctx: GraphQueryContext,
        session_data: SessionData,
        *,
        permissions: Optional[Iterable[ComputeSessionPermission]] = None,
    ) -> Self:
        status_history = session_data.status_history or {}
        raw_scheduled_at = status_history.get(SessionStatus.SCHEDULED.name)
        if not session_data.vfolder_mounts:
            vfolder_mounts = []
        else:
            vfolder_mounts = [vf.vfid.folder_id for vf in session_data.vfolder_mounts]

        if session_data.owner is None:
            raise SessionWithInvalidStateError()

        result = cls(
            # identity
            id=session_data.id,  # auto-converted to Relay global ID
            row_id=session_data.id,
            tag=session_data.tag,
            name=session_data.name,
            type=session_data.session_type,
            cluster_template=None,
            cluster_mode=session_data.cluster_mode,
            cluster_size=session_data.cluster_size,
            priority=session_data.priority,
            # ownership
            domain_name=session_data.domain_name,
            project_id=session_data.group_id,
            user_id=session_data.user_uuid,
            access_key=session_data.access_key,
            owner=UserNode.from_dataclass(ctx, session_data.owner),
            # status
            status=session_data.status.name,
            # status_changed=row.status_changed,  # FIXME: generated attribute
            status_info=session_data.status_info,
            status_data=session_data.status_data,
            status_history=status_history,
            created_at=session_data.created_at,
            starts_at=session_data.starts_at,
            terminated_at=session_data.terminated_at,
            scheduled_at=datetime.fromisoformat(raw_scheduled_at)
            if raw_scheduled_at is not None
            else None,
            startup_command=session_data.startup_command,
            result=session_data.result.name,
            # resources
            agent_ids=session_data.agent_ids,
            scaling_group=session_data.scaling_group_name,
            vfolder_mounts=vfolder_mounts,
            occupied_slots=session_data.occupying_slots,
            requested_slots=session_data.requested_slots,
            image_references=session_data.images,
            service_ports=session_data.service_ports,
            # statistics
            num_queries=session_data.num_queries,
        )
        result.permissions = [] if permissions is None else permissions
        return result

    async def resolve_idle_checks(self, info: graphene.ResolveInfo) -> dict[str, Any] | None:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, self.batch_load_idle_checks
        )
        return await loader.load(self.row_id)

    async def resolve_vfolder_nodes(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult[VirtualFolderNode]:
        ctx: GraphQueryContext = info.context
        _folder_ids = cast(list[uuid.UUID], self.vfolder_mounts)
        loader = ctx.dataloader_manager.get_loader_by_func(ctx, VirtualFolderNode.batch_load_by_id)
        result = cast(list[list[VirtualFolderNode]], await loader.load_many(_folder_ids))

        vf_nodes = cast(list[VirtualFolderNode], list(more_itertools.flatten(result)))

        # Calculate permissions for each node
        if vf_nodes:
            async with ctx.db.connect() as db_conn:
                user = ctx.user
                client_ctx = ClientContext(ctx.db, user["domain_name"], user["uuid"], user["role"])
                permission_ctx = await get_vfolder_permission_ctx(
                    db_conn, client_ctx, SystemScope(), VFolderRBACPermission.READ_ATTRIBUTE
                )

                # Load VFolderRow for each node to calculate permissions
                query = sa.select(VFolderRow).where(VFolderRow.id.in_(_folder_ids))
                async with ctx.db.begin_readonly_session(db_conn) as db_session:
                    vfolder_rows = {row.id: row for row in await db_session.scalars(query)}

                # Update permissions for each node
                for node in vf_nodes:
                    if node.row_id in vfolder_rows:
                        node.permissions = await permission_ctx.calculate_final_permission(
                            vfolder_rows[node.row_id]
                        )

        return ConnectionResolverResult(vf_nodes, None, None, None, total_count=len(vf_nodes))

    async def resolve_kernel_nodes(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult[KernelNode]:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "KernelNode.by_session_id")
        kernel_nodes = await loader.load(self.row_id)
        return ConnectionResolverResult(
            kernel_nodes, None, None, None, total_count=len(kernel_nodes)
        )

    async def resolve_resource_opts(self, info: graphene.ResolveInfo) -> dict[str, Any]:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "KernelNode.by_session_id")
        kernels = await loader.load(self.row_id)
        return {kernel.cluster_hostname: kernel.resource_opts for kernel in kernels}

    async def resolve_dependees(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult[Self]:
        ctx: GraphQueryContext = info.context
        # Get my dependees (myself is the dependent)
        loader = ctx.dataloader_manager.get_loader(ctx, "ComputeSessionNode.by_dependent_id")
        sessions = await loader.load(self.row_id)
        return ConnectionResolverResult(
            sessions,
            None,
            None,
            None,
            total_count=len(sessions),
        )

    async def resolve_dependents(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult[Self]:
        ctx: GraphQueryContext = info.context
        # Get my dependents (myself is the dependee)
        loader = ctx.dataloader_manager.get_loader(ctx, "ComputeSessionNode.by_dependee_id")
        sessions = await loader.load(self.row_id)
        return ConnectionResolverResult(
            sessions,
            None,
            None,
            None,
            total_count=len(sessions),
        )

    async def resolve_graph(
        self,
        info: graphene.ResolveInfo,
    ) -> ConnectionResolverResult[Self]:
        from ..session import SessionDependencyRow, SessionRow

        ctx: GraphQueryContext = info.context

        async with ctx.db.begin_readonly_session() as db_sess:
            dependency_cte = (
                sa.select(SessionRow.id)
                .filter(SessionRow.id == self.row_id)
                .cte(name="dependency_cte", recursive=True)
            )
            dependee = sa.select(SessionDependencyRow.depends_on).join(
                dependency_cte, SessionDependencyRow.session_id == dependency_cte.c.id
            )
            dependent = sa.select(SessionDependencyRow.session_id).join(
                dependency_cte, SessionDependencyRow.depends_on == dependency_cte.c.id
            )
            dependency_cte = dependency_cte.union_all(dependee).union_all(dependent)
            # Get the session IDs in the graph
            query = sa.select(dependency_cte.c.id)
            session_ids = (await db_sess.execute(query)).scalars().all()
            # Get the session rows in the graph
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id.in_(session_ids))
                .options(
                    selectinload(SessionRow.user),
                )
            )
            session_rows = (await db_sess.execute(query)).scalars().all()

        # Convert into GraphQL node objects
        sessions = [type(self).from_row(ctx, r) for r in session_rows]
        return ConnectionResolverResult(
            sessions,
            None,
            None,
            None,
            total_count=len(sessions),
        )

    @classmethod
    async def batch_load_idle_checks(
        cls, ctx: GraphQueryContext, session_ids: Sequence[SessionId]
    ) -> list[dict[str, ReportInfo]]:
        check_result = await ctx.idle_checker_host.get_batch_idle_check_report(session_ids)
        return [check_result[sid] for sid in session_ids]

    @classmethod
    async def batch_load_by_dependee_id(
        cls, ctx: GraphQueryContext, session_ids: Sequence[SessionId]
    ) -> Sequence[Sequence[Self]]:
        from ..session import SessionDependencyRow, SessionRow

        async with ctx.db.begin_readonly_session() as db_sess:
            j = sa.join(
                SessionRow, SessionDependencyRow, SessionRow.id == SessionDependencyRow.depends_on
            )
            query = (
                sa.select(SessionRow)
                .select_from(j)
                .where(SessionDependencyRow.session_id.in_(session_ids))
            )
            return await batch_multiresult_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.id,
            )

    @classmethod
    async def batch_load_by_dependent_id(
        cls, ctx: GraphQueryContext, session_ids: Sequence[SessionId]
    ) -> Sequence[Sequence[Self]]:
        from ..session import SessionDependencyRow, SessionRow

        async with ctx.db.begin_readonly_session() as db_sess:
            j = sa.join(
                SessionRow, SessionDependencyRow, SessionRow.id == SessionDependencyRow.session_id
            )
            query = (
                sa.select(SessionRow)
                .select_from(j)
                .where(SessionDependencyRow.depends_on.in_(session_ids))
            )
            return await batch_multiresult_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.id,
            )

    @classmethod
    async def get_accessible_node(
        cls,
        info: graphene.ResolveInfo,
        id: ResolvedGlobalID,
        scope_id: ScopeType,
        permission: ComputeSessionPermission,
    ) -> Optional[Self]:
        graph_ctx: GraphQueryContext = info.context
        user = graph_ctx.user
        client_ctx = ClientContext(graph_ctx.db, user["domain_name"], user["uuid"], user["role"])
        _, session_id = id
        async with graph_ctx.db.connect() as db_conn:
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return None
            query = sa.select(SessionRow).where(cond & (SessionRow.id == uuid.UUID(session_id)))
            query = cls._add_basic_options_to_query(query)
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
        scope_id: ScopeType,
        permission: ComputeSessionPermission,
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[Self]:
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
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = cls._add_basic_options_to_query(query.where(cond))
            cnt_query = cls._add_basic_options_to_query(cnt_query.where(cond), is_count=True)
            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                session_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
        result: list[Self] = [
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


class TotalResourceSlot(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)
        description = "Added in 25.5.0."

    occupied_slots = graphene.JSONString()
    requested_slots = graphene.JSONString()

    @classmethod
    async def get_data(
        cls,
        ctx: GraphQueryContext,
        statuses: Optional[Iterable[str]] = None,
        raw_filter: Optional[str] = None,
        domain_name: Optional[str] = None,
        resource_group_name: Optional[str] = None,
    ) -> Self:
        if statuses is not None:
            status_list = [SessionStatus[s] for s in statuses]
        else:
            status_list = None
        query_conditions: list[QueryCondition] = []
        if raw_filter is not None:
            query_conditions.append(by_raw_filter(_queryfilter_fieldspec, raw_filter))
        if status_list is not None:
            query_conditions.append(by_status(status_list))
        if domain_name is not None:
            query_conditions.append(by_domain_name(domain_name))
        if resource_group_name is not None:
            query_conditions.append(by_resource_group_name(resource_group_name))
        query_options: list[QueryOption] = [
            load_related_field(SessionRow.kernel_load_option()),
            join_by_related_field(SessionRow.user),
            join_by_related_field(SessionRow.group),
        ]
        session_rows = await SessionRow.list_session_by_condition(
            query_conditions, query_options, db=ctx.db
        )
        occupied_slots = ResourceSlot()
        requested_slots = ResourceSlot()
        for row in session_rows:
            occupied_slots += row.occupying_slots
            requested_slots += row.requested_slots
        occupied, requested = occupied_slots.to_json(), requested_slots.to_json()

        return TotalResourceSlot(
            occupied_slots=occupied,
            requested_slots=requested,
        )


def _validate_priority_input(priority: int) -> None:
    if not (SESSION_PRIORITY_MIN <= priority <= SESSION_PRIORITY_MAX):
        raise ValueError(
            f"The priority value {priority!r} is out of range: "
            f"[{SESSION_PRIORITY_MIN}, {SESSION_PRIORITY_MAX}]."
        )


def _validate_name_input(name: str) -> None:
    try:
        tx.SessionName().check(name)
    except t.DataError:
        raise ValueError(f"Not allowed session name (n:{name})")


class ModifyComputeSession(graphene.relay.ClientIDMutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)  # TODO: check if working

    class Meta:
        description = "Added in 24.09.0."

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

        priority = input.get("priority", graphql.Undefined)
        if priority:
            _validate_priority_input(priority)

        name = input.get("name", graphql.Undefined)
        if name:
            _validate_name_input(name)

        result = await graph_ctx.processors.session.modify_session.wait_for_complete(
            ModifySessionAction(
                session_id=session_id,
                modifier=SessionModifier(
                    name=OptionalState[str].from_graphql(name),
                    priority=OptionalState[int].from_graphql(priority),
                ),
            )
        )

        return ModifyComputeSession(
            ComputeSessionNode.from_dataclass(graph_ctx, result.session_data),
            input.get("client_mutation_id"),
        )


class CheckAndTransitStatusInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 24.12.0."

    ids = graphene.List(lambda: GlobalIDField, required=True)
    client_mutation_id = graphene.String(required=False)  # input for relay


class CheckAndTransitStatus(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Meta:
        description = "Added in 24.12.0"

    class Arguments:
        input = CheckAndTransitStatusInput(required=True)

    # Output fields
    item = graphene.List(lambda: ComputeSessionNode)
    client_mutation_id = graphene.String()  # Relay output

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        input: CheckAndTransitStatusInput,
    ) -> CheckAndTransitStatus:
        graph_ctx: GraphQueryContext = info.context
        session_ids = [SessionId(sid) for _, sid in input.ids]

        user_role = cast(UserRole, graph_ctx.user["role"])
        user_id = cast(uuid.UUID, graph_ctx.user["uuid"])

        session_nodes = []
        for session_id in session_ids:
            action_result = (
                await graph_ctx.processors.session.check_and_transit_status.wait_for_complete(
                    CheckAndTransitStatusAction(
                        user_id=user_id,
                        user_role=user_role,
                        session_id=session_id,
                    )
                )
            )
            session_nodes.append(
                ComputeSessionNode.from_dataclass(graph_ctx, action_result.session_data)
            )

        return CheckAndTransitStatus(session_nodes, input.get("client_mutation_id"))


class ComputeSession(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # identity
    session_id = graphene.UUID()  # identical to `id`
    main_kernel_id = graphene.UUID()
    tag = graphene.String()
    name = graphene.String()
    type = graphene.String()
    main_kernel_role = graphene.String()
    priority = graphene.Int(
        description="Added in 24.09.0.",
    )

    # image
    image = graphene.String()  # image for the main container
    architecture = graphene.String()  # image architecture for the main container
    registry = graphene.String()  # image registry for the main container
    cluster_template = graphene.String()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()

    # ownership
    domain_name = graphene.String()
    group_name = graphene.String()
    group_id = graphene.UUID()
    user_email = graphene.String()
    full_name = graphene.String()
    user_id = graphene.UUID()
    access_key = graphene.String()
    created_user_email = graphene.String()
    created_user_id = graphene.UUID()

    # status
    status = graphene.String()
    status_changed = GQLDateTime()
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
    agents = graphene.List(lambda: graphene.String)
    resource_opts = graphene.JSONString()
    scaling_group = graphene.String()
    service_ports = graphene.JSONString()
    mounts = graphene.List(lambda: graphene.String)
    vfolder_mounts = graphene.List(lambda: graphene.String)
    occupying_slots = graphene.JSONString()
    occupied_slots = graphene.JSONString()  # legacy
    requested_slots = graphene.JSONString(description="Added in 24.03.0.")

    # statistics
    num_queries = BigInt()

    # owned containers (aka kernels)
    containers = graphene.List(lambda: ComputeContainer)

    # relations
    dependencies = graphene.List(lambda: ComputeSession)

    inference_metrics = graphene.JSONString()

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: Row) -> Mapping[str, Any]:
        assert row is not None
        email = getattr(row, "email")
        full_name = getattr(row, "full_name")
        group_name = getattr(row, "group_name")
        row = row.SessionRow
        status_history = row.status_history or {}
        raw_scheduled_at = status_history.get(SessionStatus.SCHEDULED.name)
        # TODO: Deprecate 'mounts' and replace it with a list of VirtualFolderNodes
        mounts_set: set[str] = set()
        mounts: list[str] = []
        vfolder_mounts = cast(list[VFolderMount], row.vfolders_sorted_by_id)
        for mount in vfolder_mounts:
            if mount.name not in mounts_set:
                mounts.append(mount.name)
                mounts_set.add(mount.name)
        return {
            # identity
            "id": row.id,
            "session_id": row.id,
            "main_kernel_id": row.main_kernel.id,
            "tag": row.tag,
            "name": row.name,
            "type": row.session_type.name,
            "main_kernel_role": row.session_type.name,  # legacy
            "priority": row.priority,
            # image
            "image": row.images[0] if row.images is not None else "",
            "architecture": row.main_kernel.architecture,
            "registry": row.main_kernel.registry,
            "cluster_template": None,  # TODO: implement
            "cluster_mode": row.cluster_mode,
            "cluster_size": row.cluster_size,
            # ownership
            "domain_name": row.domain_name,
            "group_name": group_name[0],
            "group_id": row.group_id,
            "user_email": email,
            "full_name": full_name,
            "user_id": row.user_uuid,
            "access_key": row.access_key,
            "created_user_email": None,  # TODO: implement
            "created_user_id": None,  # TODO: implement
            # status
            "status": row.status.name,
            "status_changed": row.status_changed,
            "status_info": row.status_info,
            "status_data": row.status_data,
            "status_history": status_history,
            "created_at": row.created_at,
            "terminated_at": row.terminated_at,
            "starts_at": row.starts_at,
            "scheduled_at": (
                datetime.fromisoformat(raw_scheduled_at) if raw_scheduled_at is not None else None
            ),
            "startup_command": row.startup_command,
            "result": row.result.name,
            # resources
            "agent_ids": row.agent_ids,
            "agents": row.agent_ids,  # for backward compatibility
            "scaling_group": row.scaling_group_name,
            "service_ports": row.main_kernel.service_ports,
            "mounts": [*{mount.name for mount in vfolder_mounts}],
            # TODO: Deprecate 'vfolder_mounts' and replace it with a list of VirtualFolderNodes
            "vfolder_mounts": [*{vf.vfid.folder_id for vf in vfolder_mounts}],
            "occupying_slots": row.occupying_slots.to_json(),
            "occupied_slots": row.occupying_slots.to_json(),
            "requested_slots": row.requested_slots.to_json(),
            # statistics
            "num_queries": row.num_queries,
        }

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row | None) -> ComputeSession | None:
        if row is None:
            return None
        props = cls.parse_row(ctx, row)
        return cls(**props)

    async def resolve_inference_metrics(
        self, info: graphene.ResolveInfo
    ) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "KernelStatistics.inference_metrics_by_kernel"
        )
        return await loader.load(self.id)

    async def resolve_containers(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[ComputeContainer]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "ComputeContainer.by_session")
        return await loader.load(self.session_id)

    async def resolve_dependencies(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[ComputeSession]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "ComputeSession.by_dependency")
        return await loader.load(self.id)

    async def resolve_commit_status(self, info: graphene.ResolveInfo) -> str:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "ComputeSession.commit_statuses"
        )
        return await loader.load(self.main_kernel_id)

    async def resolve_resource_opts(self, info: graphene.ResolveInfo) -> dict[str, Any]:
        containers = self.containers
        if containers is None:
            containers = await self.resolve_containers(info)
        if containers is None:
            return {}
        self.containers = containers
        return {cntr.cluster_hostname: cntr.resource_opts for cntr in containers}

    async def resolve_abusing_reports(
        self, info: graphene.ResolveInfo
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        containers = self.containers
        if containers is None:
            containers = await self.resolve_containers(info)
        if containers is None:
            return []
        self.containers = containers
        return [(await con.resolve_abusing_report(info, self.access_key)) for con in containers]

    async def resolve_idle_checks(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        graph_ctx: GraphQueryContext = info.context
        return await graph_ctx.idle_checker_host.get_idle_check_report(self.session_id)

    _queryfilter_fieldspec: FieldSpecType = {
        "id": ("sessions_id", None),
        "type": ("sessions_session_type", SessionTypes),
        "name": ("sessions_name", None),
        "priority": ("sessions_priority", None),
        "image": (ArrayFieldItem("sessions_images"), None),
        "agent_ids": (ArrayFieldItem("sessions_agent_ids"), None),
        "agent_id": (ArrayFieldItem("sessions_agent_ids"), None),
        "agents": (ArrayFieldItem("sessions_agent_ids"), None),  # for backward compatibility
        "domain_name": ("sessions_domain_name", None),
        "group_name": ("group_name", None),
        "user_email": ("users_email", None),
        "user_id": ("sessions_user_uuid", None),
        "full_name": ("users_full_name", None),
        "access_key": ("sessions_access_key", None),
        "scaling_group": ("sessions_scaling_group_name", None),
        "cluster_mode": ("sessions_cluster_mode", ClusterMode),
        "cluster_size": ("sessions_cluster_size", None),
        "status": ("sessions_status", SessionStatus),
        "status_info": ("sessions_status_info", None),
        "result": ("sessions_result", SessionResult),
        "created_at": ("sessions_created_at", dtparse),
        "terminated_at": ("sessions_terminated_at", dtparse),
        "starts_at": ("sessions_starts_at", dtparse),
        "scheduled_at": (
            JSONFieldItem("sessions_status_history", SessionStatus.SCHEDULED.name),
            dtparse,
        ),
        "startup_command": ("sessions_startup_command", None),
    }

    _queryorder_colmap: ColumnMapType = {
        "id": ("sessions_id", None),
        "type": ("sessions_session_type", None),
        "name": ("sessions_name", None),
        "image": ("sessions_images", None),
        "priority": ("sessions_priority", None),
        "agent_ids": ("sessions_agent_ids", None),
        "agent_id": ("sessions_agent_ids", None),
        "agents": ("sessions_agent_ids", None),
        "domain_name": ("sessions_domain_name", None),
        "group_name": ("group_name", None),
        "user_email": ("users_email", None),
        "user_id": ("sessions_user_uuid", None),
        "full_name": ("users_full_name", None),
        "access_key": ("sessions_access_key", None),
        "scaling_group": ("sessions_scaling_group_name", None),
        "cluster_mode": ("sessions_cluster_mode", None),
        # "cluster_template": "cluster_template",
        "cluster_size": ("sessions_cluster_size", None),
        "status": ("sessions_status", None),
        "status_info": ("sessions_status_info", None),
        "result": ("sessions_result", None),
        "created_at": ("sessions_created_at", None),
        "terminated_at": ("sessions_terminated_at", None),
        "starts_at": ("sessions_starts_at", None),
        "scheduled_at": (
            JSONFieldItem("sessions_status_history", SessionStatus.SCHEDULED.name),
            None,
        ),
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[str] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> int:
        if isinstance(status, str):
            status_list = [SessionStatus[s] for s in status.split(",")]
        elif isinstance(status, SessionStatus):
            status_list = [status]
        j = (
            # joins with GroupRow and UserRow do not need to be LEFT OUTER JOIN since those foreign keys are not nullable.
            sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id)
            .join(UserRow, SessionRow.user_uuid == UserRow.uuid)
            .join(KernelRow, SessionRow.id == KernelRow.session_id)
        )
        query = sa.select([sa.func.count(sa.distinct(SessionRow.id))]).select_from(j)
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(SessionRow.group_id == group_id)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        if status is not None:
            query = query.where(SessionRow.status.in_(status_list))
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[str] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[ComputeSession | None]:
        if status is None:
            status_list = None
        elif isinstance(status, str):
            status_list = [SessionStatus[s] for s in status.split(",")]
        elif isinstance(status, SessionStatus):
            status_list = [status]
        j = (
            # joins with GroupRow and UserRow do not need to be LEFT OUTER JOIN since those foreign keys are not nullable.
            sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id).join(
                UserRow, SessionRow.user_uuid == UserRow.uuid
            )
        )
        query = (
            sa.select(
                SessionRow,
                agg_to_array(GroupRow.name).label("group_name"),
                UserRow.email,
                UserRow.full_name,
            )
            .select_from(j)
            .options(selectinload(SessionRow.kernels.and_(KernelRow.cluster_role == DEFAULT_ROLE)))
            .group_by(SessionRow, UserRow.email, UserRow.full_name)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(SessionRow.group_id == group_id)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        if status is not None:
            query = query.where(SessionRow.status.in_(status_list))
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(*DEFAULT_SESSION_ORDERING)
        async with ctx.db.begin_readonly_session() as db_sess:
            return [cls.from_row(ctx, r) async for r in (await db_sess.stream(query))]

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[str] = None,
    ) -> Sequence[ComputeSession | None]:
        j = sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id).join(
            UserRow, SessionRow.user_uuid == UserRow.uuid
        )
        query = (
            sa.select(
                SessionRow,
                GroupRow.name.label("group_name"),
                UserRow.email,
                UserRow.full_name,
            )
            .select_from(j)
            .where(SessionRow.id.in_(session_ids))
            .options(selectinload(SessionRow.kernels))
        )
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        async with ctx.db.begin_readonly_session() as db_sess:
            return await batch_result_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.SessionRow.id,
            )

    @classmethod
    async def batch_load_by_dependency(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Sequence[ComputeSession]]:
        j = sa.join(
            SessionRow,
            SessionDependencyRow,
            SessionRow.id == SessionDependencyRow.depends_on,
        )
        query = (
            sa.select(SessionRow)
            .select_from(j)
            .where(SessionDependencyRow.session_id.in_(session_ids))
            .options(selectinload(SessionRow.kernels))
        )
        async with ctx.db.begin_readonly_session() as db_sess:
            return await batch_multiresult_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.SessionRow.id,
            )

    @classmethod
    async def batch_load_commit_statuses(
        cls,
        ctx: GraphQueryContext,
        kernel_ids: Sequence[KernelId],
    ) -> Sequence[str]:
        commit_statuses = await ctx.registry.get_commit_status(kernel_ids)
        return [commit_statuses[kernel_id] for kernel_id in kernel_ids]


class ComputeSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(ComputeSession, required=True)


class InferenceSession(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)


class InferenceSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(InferenceSession, required=True)

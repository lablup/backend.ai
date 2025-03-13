from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Self,
    Sequence,
)

import graphene
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime

from ai.backend.manager.models.rbac import ProjectScope

from ..base import (
    BigInt,
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
)
from ..group import AssocGroupUserRow, GroupRow, ProjectType, get_permission_ctx
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..rbac.context import ClientContext
from ..rbac.permission_defs import ProjectPermission
from .user import UserConnection, UserNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext
    from ..rbac import ContainerRegistryScope, ScopeType
    from ..scaling_group import ScalingGroup

_queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
    "id": ("id", None),
    "row_id": ("id", None),
    "name": ("name", None),
    "is_active": ("is_active", None),
    "created_at": ("created_at", dtparse),
    "modified_at": ("modified_at", dtparse),
    "domain_name": ("domain_name", None),
    "resource_policy": ("resource_policy", None),
}

_queryorder_colmap: Mapping[str, OrderSpecItem] = {
    "id": ("id", None),
    "row_id": ("id", None),
    "name": ("name", None),
    "is_active": ("is_active", None),
    "created_at": ("created_at", None),
    "modified_at": ("modified_at", None),
    "domain_name": ("domain_name", None),
    "resource_policy": ("resource_policy", None),
}


class GroupInput(graphene.InputObjectType):
    type = graphene.String(
        required=False,
        default_value="GENERAL",
        description=(
            f"Added in 24.03.0. Available values: {', '.join([p.name for p in ProjectType])}"
        ),
    )
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    domain_name = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    integration_id = graphene.String(required=False, default_value="")
    resource_policy = graphene.String(required=False, default_value="default")
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )


class ModifyGroupInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    domain_name = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    user_update_mode = graphene.String(required=False)
    user_uuids = graphene.List(lambda: graphene.String, required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    integration_id = graphene.String(required=False)
    resource_policy = graphene.String(required=False)
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )


class GroupNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    row_id = graphene.UUID(description="Added in 24.03.7. The undecoded id value stored in DB.")
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    integration_id = graphene.String()
    resource_policy = graphene.String()
    type = graphene.String(description=f"Added in 24.03.7. One of {[t.name for t in ProjectType]}.")
    container_registry = graphene.JSONString(description="Added in 24.03.7.")
    scaling_groups = graphene.List(
        lambda: graphene.String,
    )

    registry_quota = BigInt(description="Added in 25.3.0.")

    user_nodes = PaginatedConnectionField(
        UserConnection,
    )

    @classmethod
    def from_row(
        cls,
        graph_ctx: GraphQueryContext,
        row: GroupRow,
    ) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            total_resource_slots=row.total_resource_slots.to_json() or {},
            allowed_vfolder_hosts=row.allowed_vfolder_hosts.to_json() or {},
            integration_id=row.integration_id,
            resource_policy=row.resource_policy,
            type=row.type.name,
            container_registry=row.container_registry,
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    async def resolve_user_nodes(
        self,
        info: graphene.ResolveInfo,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        from ..user import UserRow

        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter, QueryFilterParser(UserNode._queryfilter_fieldspec))
            if filter is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order, QueryOrderParser(UserNode._queryorder_colmap))
            if order is not None
            else None
        )
        (
            query,
            _,
            conditions,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            UserRow,
            UserRow.uuid,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        j = sa.join(UserRow, AssocGroupUserRow)
        user_query = query.select_from(j).where(AssocGroupUserRow.group_id == self.id)
        cnt_query = (
            sa.select(sa.func.count()).select_from(j).where(AssocGroupUserRow.group_id == self.id)
        )
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            user_rows = (await db_session.scalars(user_query)).all()
            result = [type(self).from_row(graph_ctx, row) for row in user_rows]
            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    async def resolve_registry_quota(self, info: graphene.ResolveInfo) -> int:
        graph_ctx: GraphQueryContext = info.context
        scope_id = ProjectScope(project_id=self.id, domain_name=None)

        return await graph_ctx.services_ctx.per_project_container_registries_quota.read_quota(
            scope_id,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id) -> Self:
        graph_ctx: GraphQueryContext = info.context
        _, group_id = AsyncNode.resolve_global_id(info, id)
        query = sa.select(GroupRow).where(GroupRow.id == group_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            group_row = (await db_session.scalars(query)).first()
            return cls.from_row(graph_ctx, group_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        scope: ScopeType,
        container_registry_scope: Optional[ContainerRegistryScope] = None,
        permission: ProjectPermission = ProjectPermission.READ_ATTRIBUTE,
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
            GroupRow,
            GroupRow.id,
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
            permission_ctx = await get_permission_ctx(
                db_conn, client_ctx, permission, scope, container_registry_scope
            )
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond)
            cnt_query = cnt_query.where(cond)

            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                group_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
                result = [cls.from_row(graph_ctx, row) for row in group_rows]

        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class GroupConnection(Connection):
    class Meta:
        node = GroupNode
        description = "Added in 24.03.0"


class GroupPermissionField(graphene.Scalar):
    class Meta:
        description = f"Added in 25.3.0. One of {[val.value for val in ProjectPermission]}."

    @staticmethod
    def serialize(val: ProjectPermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ProjectPermission(node.value)

    @staticmethod
    def parse_value(value: str) -> ProjectPermission:
        return ProjectPermission(value)

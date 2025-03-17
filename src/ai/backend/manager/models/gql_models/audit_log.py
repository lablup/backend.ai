from typing import TYPE_CHECKING, Mapping, Optional, Self, cast

import graphene

from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
)
from ai.backend.manager.models.gql_relay import AsyncNode, ConnectionResolverResult
from ai.backend.manager.models.minilang import FieldSpecItem, OrderSpecItem
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser

from ..gql_relay import Connection

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


class AuditLogNode(graphene.ObjectType):
    """
    Added in 25.5.0.
    """

    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.5.0."

    row_id = graphene.UUID()
    name = graphene.String()
    operation = graphene.String()
    status = graphene.String()
    created_at = graphene.DateTime()
    duration = graphene.String()
    description = graphene.String()
    entity_type = graphene.String()
    entity_id = graphene.String()

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "name": ("name", None),
        "operation": ("operation", None),
        "status": ("status", None),
        "created_at": ("created_at", None),
        "duration": ("duration", None),
        "description": ("description", None),
        "entity_type": ("entity_type", None),
        "entity_id": ("entity_id", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "name": ("name", None),
        "operation": ("operation", None),
        "status": ("status", None),
        "created_at": ("created_at", None),
        "duration": ("duration", None),
        "description": ("description", None),
        "entity_type": ("entity_type", None),
        "entity_id": ("entity_id", None),
    }

    @classmethod
    def from_row(cls, ctx, row: AuditLogRow) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            operation=row.operation,
            status=row.status,
            created_at=row.created_at,
            duration=row.duration,
            description=row.description,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
        )

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
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
            FilterExprArg(filter_expr, QueryFilterParser(cls._queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls._queryorder_colmap))
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
            AuditLogRow,
            AuditLogRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_rows = await db_session.scalars(query)
            total_cnt = await db_session.scalar(cnt_query)
        result = [cls.from_row(graph_ctx, cast(AuditLogRow, row)) for row in reg_rows]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class AuditLogConnection(Connection):
    """Added in 25.5.0."""

    class Meta:
        node = AuditLogNode
        description = "Added in 25.5.0."

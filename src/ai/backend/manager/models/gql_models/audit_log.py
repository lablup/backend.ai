from datetime import timedelta
from typing import TYPE_CHECKING, Mapping, Optional, Self, cast

import graphene
from dateutil.parser import parse as dtparse

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.models.audit_log import (
    AuditLogEntityType,
    AuditLogRow,
)
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


class AuditLogSchema(graphene.ObjectType):
    """
    A schema that contains metadata related to the AuditLogNode.
    It provides a list of values, such as entity_type and status, that can be used in the AuditLog, allowing clients to retrieve them.

    Added in 25.6.0.
    """

    entity_type_variants = graphene.List(
        graphene.String, description='Possible values of "AuditLogNode.entity_type"'
    )
    status_variants = graphene.List(
        graphene.String, description='Possible values of "AuditLogNode.status"'
    )

    async def resolve_entity_type_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return list(AuditLogEntityType.__members__.values())

    async def resolve_status_variants(self, info: graphene.ResolveInfo) -> list[str]:
        return list(OperationStatus.__members__.values())


class AuditLogNode(graphene.ObjectType):
    """
    Added in 25.6.0.
    """

    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.6.0."

    row_id = graphene.UUID(required=True, description="UUID of the AuditLog row")
    action_id = graphene.UUID(required=True, description="Added in 25.6.0. UUID of the action")
    entity_type = graphene.String(required=True, description="Entity type of the AuditLog")
    operation = graphene.String(required=True, description="Operation type of the AuditLog")
    entity_id = graphene.String(required=False, description="Entity ID of the AuditLog")
    created_at = graphene.DateTime(required=True, description="The time the AuditLog was reported")
    request_id = graphene.String(required=False, description="Request ID of the AuditLog")
    triggered_by = graphene.String(
        required=False, description="Added in 25.12.0, User ID that triggered the action"
    )
    description = graphene.String(required=True, description="Description of the AuditLog")
    duration = graphene.String(
        required=False, description="Duration taken to perform the operation"
    )
    status = graphene.String(required=True, description="Status of the AuditLog")

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "entity_type": ("entity_type", None),
        "action_id": ("action_id", None),
        "operation": ("operation", None),
        "entity_id": ("entity_id", None),
        "created_at": ("created_at", dtparse),
        "request_id": ("request_id", None),
        "triggered_by": ("triggered_by", None),
        "description": ("description", None),
        "duration": ("duration", lambda duration: timedelta(seconds=float(duration))),
        "status": ("status", OperationStatus),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "entity_type": ("entity_type", None),
        "action_id": ("action_id", None),
        "operation": ("operation", None),
        "entity_id": ("entity_id", None),
        "created_at": ("created_at", None),
        "request_id": ("request_id", None),
        "triggered_by": ("triggered_by", None),
        "description": ("description", None),
        "duration": ("duration", None),
        "status": ("status", None),
    }

    @classmethod
    def from_row(cls, ctx, row: AuditLogRow) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            entity_type=row.entity_type,
            operation=row.operation,
            entity_id=row.entity_id,
            created_at=row.created_at,
            action_id=row.action_id,
            request_id=row.request_id,
            triggered_by=row.triggered_by,
            description=row.description,
            duration=row.duration,
            status=row.status,
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
            auditlog_rows = await db_session.scalars(query)
            total_cnt = await db_session.scalar(cnt_query)
        result = [cls.from_row(graph_ctx, cast(AuditLogRow, row)) for row in auditlog_rows]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class AuditLogConnection(Connection):
    """Added in 25.6.0."""

    class Meta:
        node = AuditLogNode
        description = "Added in 25.6.0."

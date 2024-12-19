import decimal
import uuid
from typing import TYPE_CHECKING, Mapping, Self

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.api.exceptions import (
    GenericForbidden,
    InvalidAPIParameters,
    ObjectNotFound,
)

from ..base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
    gql_mutation_wrapper,
    set_if_set,
)
from ..endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointRow,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..user import UserRole

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


_queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
    "id": ("id", None),
    "metric_source": ("metric_source", None),
    "metric_name": ("metric_name", None),
    "threshold": ("threshold", None),
    "comparator": ("comparator", None),
    "step_size": ("step_size", None),
    "cooldown_seconds": ("cooldown_seconds", None),
    "created_at": ("created_at", dtparse),
    "last_triggered_at": ("last_triggered_at", dtparse),
    "endpoint": ("endpoint", None),
}

_queryorder_colmap: Mapping[str, OrderSpecItem] = {
    "id": ("id", None),
    "metric_source": ("metric_source", None),
    "metric_name": ("metric_name", None),
    "threshold": ("threshold", None),
    "comparator": ("comparator", None),
    "step_size": ("step_size", None),
    "cooldown_seconds": ("cooldown_seconds", None),
    "created_at": ("created_at", None),
    "last_triggered_at": ("last_triggered_at", None),
    "endpoint": ("endpoint", None),
}


class EndpointAutoScalingRuleNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.12.0."

    row_id = graphene.UUID(required=True, description="Added in 24.12.0.")

    metric_source = graphene.String(required=True, description="Added in 24.12.0.")
    metric_name = graphene.String(required=True, description="Added in 24.12.0.")
    threshold = graphene.String(required=True, description="Added in 24.12.0.")
    comparator = graphene.String(required=True, description="Added in 24.12.0.")
    step_size = graphene.Int(required=True, description="Added in 24.12.0.")
    cooldown_seconds = graphene.Int(required=True, description="Added in 24.12.0.")

    created_at = GQLDateTime(required=True, description="Added in 24.12.0.")
    last_triggered_at = GQLDateTime(description="Added in 24.12.0.")

    endpoint = graphene.UUID(required=True, description="Added in 24.12.0.")

    @classmethod
    def from_row(
        cls, graph_ctx: GraphQueryContext, row: EndpointAutoScalingRuleRow
    ) -> "EndpointAutoScalingRuleNode":
        return EndpointAutoScalingRuleNode(
            id=row.id,
            row_id=row.id,
            metric_source=row.metric_source.name,
            metric_name=row.metric_name,
            threshold=row.threshold,
            comparator=row.comparator.name,
            step_size=row.step_size,
            cooldown_seconds=row.cooldown_seconds,
            created_at=row.created_at,
            last_triggered_at=row.last_triggered_at,
            endpoint=row.endpoint,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> "EndpointAutoScalingRuleNode":
        graph_ctx: GraphQueryContext = info.context

        _, rule = AsyncNode.resolve_global_id(info, id)
        query = sa.select(EndpointAutoScalingRuleRow).where(EndpointAutoScalingRuleRow.id == rule)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            rule_row = await db_session.scalar(query)
            if rule_row is None:
                raise ValueError(f"Rule not found (id: {rule})")
            return cls.from_row(graph_ctx, rule_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        *,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
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
            EndpointAutoScalingRuleRow,
            EndpointAutoScalingRuleRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            group_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(graph_ctx, row) for row in group_rows]
            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class EndpointAutoScalingRuleConnection(Connection):
    class Meta:
        node = EndpointAutoScalingRuleNode
        description = "Added in 24.12.0."


class EndpointAutoScalingRuleInput(graphene.InputObjectType):
    metric_source = graphene.String(
        required=True,
        description=(
            f"Added in 24.12.0. Available values: {", ".join([p.name for p in AutoScalingMetricSource])}"
        ),
    )
    metric_name = graphene.String(required=True, description="Added in 24.12.0.")
    threshold = graphene.String(required=True, description="Added in 24.12.0.")
    comparator = graphene.String(
        required=True,
        description=(
            f"Added in 24.12.0. Available values: {", ".join([p.name for p in AutoScalingMetricComparator])}"
        ),
    )
    step_size = graphene.Int(required=True, description="Added in 24.12.0.")
    cooldown_seconds = graphene.Int(required=True, description="Added in 24.12.0.")


class ModifyEndpointAutoScalingRuleInput(graphene.InputObjectType):
    metric_source = graphene.String(
        description=(
            f"Added in 24.12.0. Available values: {", ".join([p.name for p in AutoScalingMetricSource])}"
        )
    )
    metric_name = graphene.String(description="Added in 24.12.0.")
    threshold = graphene.String(description="Added in 24.12.0.")
    comparator = graphene.String(
        description=(
            f"Added in 24.12.0. Available values: {", ".join([p.name for p in AutoScalingMetricComparator])}"
        )
    )
    step_size = graphene.Int(description="Added in 24.12.0.")
    cooldown_seconds = graphene.Int(description="Added in 24.12.0.")


class CreateEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        endpoint_id = graphene.String(required=True)
        props = EndpointAutoScalingRuleInput(required=True)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        endpoint_id: str,
        props: EndpointAutoScalingRuleInput,
    ) -> "CreateEndpointAutoScalingRuleNode":
        _, raw_endpoint_id = AsyncNode.resolve_global_id(info, endpoint_id)
        if not raw_endpoint_id:
            raw_endpoint_id = endpoint_id

        try:
            _endpoint_id = uuid.UUID(raw_endpoint_id)
        except ValueError:
            raise ObjectNotFound("endpoint")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointRow.get(db_session, _endpoint_id)
            except NoResultFound:
                raise ObjectNotFound(object_name="endpoint")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            try:
                _source = AutoScalingMetricSource[props.metric_source]
            except ValueError:
                raise InvalidAPIParameters(
                    f"Unsupported AutoScalingMetricSource {props.metric_source}"
                )
            try:
                _comparator = AutoScalingMetricComparator[props.comparator]
            except ValueError:
                raise InvalidAPIParameters(
                    f"Unsupported AutoScalingMetricComparator {props.comparator}"
                )
            try:
                _threshold = decimal.Decimal(props.threshold)
            except decimal.InvalidOperation:
                raise InvalidAPIParameters(f"Cannot convert {props.threshold} to Decimal")

            async def _do_mutate() -> CreateEndpointAutoScalingRuleNode:
                created_rule = await row.create_auto_scaling_rule(
                    db_session,
                    _source,
                    props.name,
                    _threshold,
                    _comparator,
                    props.step_size,
                    props.cooldown_seconds,
                )
                return CreateEndpointAutoScalingRuleNode(
                    ok=True,
                    msg="Auto scaling rule created",
                    network=EndpointAutoScalingRuleNode.from_row(info.context, created_rule),
                )

            return await gql_mutation_wrapper(CreateEndpointAutoScalingRuleNode, _do_mutate)


class ModifyEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        id = graphene.String(required=True)
        props = ModifyEndpointAutoScalingRuleInput(required=True)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        props: ModifyEndpointAutoScalingRuleInput,
    ) -> "ModifyEndpointAutoScalingRuleNode":
        _, rule_id = AsyncNode.resolve_global_id(info, id)
        if not rule_id:
            rule_id = id

        try:
            _rule_id = uuid.UUID(rule_id)
        except ValueError:
            raise ObjectNotFound("auto_scaling_rule")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise ObjectNotFound(object_name="auto_scaling_rule")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            async def _do_mutate() -> CreateEndpointAutoScalingRuleNode:
                if (_newval := props.metric_source) and _newval is not Undefined:
                    try:
                        row.metric_source = AutoScalingMetricSource[_newval]
                    except ValueError:
                        raise InvalidAPIParameters(f"Unsupported AutoScalingMetricSource {_newval}")
                if (_newval := props.comparator) and _newval is not Undefined:
                    try:
                        row.comparator = AutoScalingMetricComparator[_newval]
                    except ValueError:
                        raise InvalidAPIParameters(
                            f"Unsupported AutoScalingMetricComparator {_newval}"
                        )
                if (_newval := props.threshold) and _newval is not Undefined:
                    try:
                        row.threshold = decimal.Decimal(_newval)
                    except decimal.InvalidOperation:
                        raise InvalidAPIParameters(f"Cannot convert {_newval} to Decimal")

                set_if_set(props, row, "metric_name")
                set_if_set(props, row, "step_size")
                set_if_set(props, row, "cooldown_seconds")

                return ModifyEndpointAutoScalingRuleNode(
                    ok=True,
                    msg="Auto scaling rule updated",
                    network=EndpointAutoScalingRuleNode.from_row(info.context, row),
                )

            return await gql_mutation_wrapper(ModifyEndpointAutoScalingRuleNode, _do_mutate)


class DeleteEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        id = graphene.String(required=True)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
    ) -> "DeleteEndpointAutoScalingRuleNode":
        _, rule_id = AsyncNode.resolve_global_id(info, id)
        if not rule_id:
            rule_id = id

        try:
            _rule_id = uuid.UUID(rule_id)
        except ValueError:
            raise ObjectNotFound("auto_scaling_rule")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise ObjectNotFound(object_name="auto_scaling_rule")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            async def _do_mutate() -> DeleteEndpointAutoScalingRuleNode:
                db_session.delete(row)

                return DeleteEndpointAutoScalingRuleNode(
                    ok=True,
                    msg="Auto scaling rule removed",
                )

            return await gql_mutation_wrapper(DeleteEndpointAutoScalingRuleNode, _do_mutate)

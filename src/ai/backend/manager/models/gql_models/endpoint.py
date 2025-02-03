from __future__ import annotations

import decimal
from typing import TYPE_CHECKING, Mapping, Self
from uuid import UUID

import graphene
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointId,
    RuleId,
)

from ...api.exceptions import (
    GenericForbidden,
    InvalidAPIParameters,
    ObjectNotFound,
)
from ..base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
    gql_mutation_wrapper,
    orm_set_if_set,
)
from ..endpoint import (
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


AutoScalingMetricSourceGQLEnum = graphene.Enum.from_enum(
    AutoScalingMetricSource,
    description="The source type to fetch metrics. Added in 25.1.0.",
)
AutoScalingMetricComparatorGQLEnum = graphene.Enum.from_enum(
    AutoScalingMetricComparator,
    description="The comparator used to compare the metric value with the threshold. Added in 25.1.0.",
)


class EndpointAutoScalingRuleNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.1.0."

    row_id = graphene.UUID(required=True)

    metric_source = graphene.Field(
        AutoScalingMetricSourceGQLEnum,
        required=True,
    )
    metric_name = graphene.String(required=True)
    threshold = graphene.String(required=True)
    comparator = graphene.Field(
        AutoScalingMetricComparatorGQLEnum,
        required=True,
    )
    step_size = graphene.Int(required=True)
    cooldown_seconds = graphene.Int(required=True)

    min_replicas = graphene.Int()
    max_replicas = graphene.Int()

    created_at = GQLDateTime(required=True)
    last_triggered_at = GQLDateTime()

    endpoint = graphene.UUID(required=True)

    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: EndpointAutoScalingRuleRow) -> Self:
        return cls(
            id=row.id,
            row_id=row.id,
            metric_source=row.metric_source,
            metric_name=row.metric_name,
            threshold=row.threshold,
            comparator=row.comparator,
            step_size=row.step_size,
            cooldown_seconds=row.cooldown_seconds,
            min_replicas=row.min_replicas,
            max_replicas=row.max_replicas,
            created_at=row.created_at,
            last_triggered_at=row.last_triggered_at,
            endpoint=row.endpoint,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, rule_id: str) -> Self:
        graph_ctx: GraphQueryContext = info.context

        _, raw_rule_id = AsyncNode.resolve_global_id(info, rule_id)
        if not raw_rule_id:
            raw_rule_id = rule_id
        try:
            _rule_id = RuleId(UUID(raw_rule_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

        async with graph_ctx.db.begin_readonly_session() as db_session:
            rule_row = await EndpointAutoScalingRuleRow.get(
                db_session, _rule_id, load_endpoint=True
            )
            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if rule_row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if rule_row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            return cls.from_row(graph_ctx, rule_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        endpoint: str,
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
            _, raw_endpoint_id = AsyncNode.resolve_global_id(info, endpoint)
            if not raw_endpoint_id:
                raw_endpoint_id = endpoint
            try:
                _endpoint_id = EndpointId(UUID(raw_endpoint_id))
            except ValueError:
                raise ObjectNotFound(object_name="Endpoint")
            try:
                row = await EndpointRow.get(db_session, _endpoint_id)
            except NoResultFound:
                raise ObjectNotFound(object_name="Endpoint")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            query = query.filter(EndpointAutoScalingRuleRow.endpoint == _endpoint_id)
            group_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(graph_ctx, row) for row in group_rows]
            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class EndpointAutoScalingRuleConnection(Connection):
    class Meta:
        node = EndpointAutoScalingRuleNode
        description = "Added in 25.1.0."


class EndpointAutoScalingRuleInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 25.1.0."

    metric_source = graphene.Field(
        AutoScalingMetricSourceGQLEnum,
        required=True,
    )
    metric_name = graphene.String(required=True)
    threshold = graphene.String(required=True)
    comparator = graphene.Field(
        AutoScalingMetricComparatorGQLEnum,
        required=True,
    )
    step_size = graphene.Int(required=True)
    cooldown_seconds = graphene.Int(required=True)
    min_replicas = graphene.Int()
    max_replicas = graphene.Int()


class ModifyEndpointAutoScalingRuleInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 25.1.0."

    metric_source = graphene.Field(
        AutoScalingMetricSourceGQLEnum,
        default_value=Undefined,
    )
    metric_name = graphene.String()
    threshold = graphene.String()
    comparator = graphene.Field(
        AutoScalingMetricComparatorGQLEnum,
        default_value=Undefined,
    )
    step_size = graphene.Int()
    cooldown_seconds = graphene.Int()
    min_replicas = graphene.Int()
    max_replicas = graphene.Int()


class CreateEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        endpoint = graphene.String(required=True)
        props = EndpointAutoScalingRuleInput(required=True)

    class Meta:
        description = "Added in 25.1.0."

    ok = graphene.Boolean()
    msg = graphene.String()
    rule = graphene.Field(lambda: EndpointAutoScalingRuleNode, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        endpoint: str,
        props: EndpointAutoScalingRuleInput,
    ) -> Self:
        _, raw_endpoint_id = AsyncNode.resolve_global_id(info, endpoint)
        if not raw_endpoint_id:
            raw_endpoint_id = endpoint
        if not props.metric_source:
            raise InvalidAPIParameters("metric_source is a required field")
        if not props.comparator:
            raise InvalidAPIParameters("comparator is a required field")

        try:
            _endpoint_id = EndpointId(UUID(raw_endpoint_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointRow.get(db_session, _endpoint_id)
            except NoResultFound:
                raise ObjectNotFound(object_name="Endpoint")

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
                _threshold = decimal.Decimal(props.threshold)
            except decimal.InvalidOperation:
                raise InvalidAPIParameters(f"Cannot convert {props.threshold} to Decimal")

            async def _do_mutate() -> Self:
                created_rule = await row.create_auto_scaling_rule(
                    db_session,
                    props.metric_source,
                    props.metric_name,
                    _threshold,
                    props.comparator,
                    props.step_size,
                    cooldown_seconds=props.cooldown_seconds,
                    min_replicas=props.min_replicas,
                    max_replicas=props.max_replicas,
                )
                return cls(
                    ok=True,
                    msg="Auto scaling rule created",
                    rule=EndpointAutoScalingRuleNode.from_row(info.context, created_rule),
                )

            return await gql_mutation_wrapper(cls, _do_mutate)


class ModifyEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        id = graphene.String(required=True)
        props = ModifyEndpointAutoScalingRuleInput(required=True)

    class Meta:
        description = "Added in 25.1.0."

    ok = graphene.Boolean()
    msg = graphene.String()
    rule = graphene.Field(lambda: EndpointAutoScalingRuleNode, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        props: ModifyEndpointAutoScalingRuleInput,
    ) -> Self:
        _, rule_id = AsyncNode.resolve_global_id(info, id)
        if not rule_id:
            rule_id = id

        try:
            _rule_id = RuleId(UUID(rule_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            async def _do_mutate() -> Self:
                if (_newval := props.threshold) and _newval is not Undefined:
                    try:
                        row.threshold = decimal.Decimal(_newval)
                    except decimal.InvalidOperation:
                        raise InvalidAPIParameters(f"Cannot convert {_newval} to Decimal")

                orm_set_if_set(props, row, "metric_source")
                orm_set_if_set(props, row, "metric_name")
                orm_set_if_set(props, row, "comparator")
                orm_set_if_set(props, row, "step_size")
                orm_set_if_set(props, row, "cooldown_seconds")
                orm_set_if_set(props, row, "min_replicas")
                orm_set_if_set(props, row, "max_replicas")

                return cls(
                    ok=True,
                    msg="Auto scaling rule updated",
                    rule=EndpointAutoScalingRuleNode.from_row(info.context, row),
                )

            return await gql_mutation_wrapper(cls, _do_mutate)


class DeleteEndpointAutoScalingRuleNode(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        id = graphene.String(required=True)

    class Meta:
        description = "Added in 25.1.0."

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
    ) -> Self:
        _, rule_id = AsyncNode.resolve_global_id(info, id)
        if not rule_id:
            rule_id = id

        try:
            _rule_id = RuleId(UUID(rule_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != graph_ctx.user["uuid"]:
                        raise GenericForbidden

            async def _do_mutate() -> Self:
                await db_session.delete(row)
                return cls(
                    ok=True,
                    msg="Auto scaling rule removed",
                )

            return await gql_mutation_wrapper(cls, _do_mutate)

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Mapping, Self
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
from ai.backend.manager.models.utils import define_state
from ai.backend.manager.services.model_service.actions.create_endpoint_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_service.actions.delete_enpoint_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_service.actions.modify_endpoint_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_service.types import (
    EndpointAutoScalingRuleData,
    RequesterCtx,
)
from ai.backend.manager.types import OptionalState, TriState

from ...api.exceptions import (
    GenericForbidden,
    ObjectNotFound,
)
from ..base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
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
    def from_dto(cls, dto: EndpointAutoScalingRuleData) -> Self:
        return cls(
            id=dto.id,
            row_id=dto.id,
            metric_source=dto.metric_source,
            metric_name=dto.metric_name,
            threshold=dto.threshold,
            comparator=dto.comparator,
            step_size=dto.step_size,
            cooldown_seconds=dto.cooldown_seconds,
            min_replicas=dto.min_replicas,
            max_replicas=dto.max_replicas,
            created_at=dto.created_at,
            last_triggered_at=dto.last_triggered_at,
            endpoint=dto.endpoint,
        )

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
                    if row.domain != graph_ctx.user["domain_name"]:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.created_user != graph_ctx.user["uuid"]:
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

    def to_action(
        self, requester_ctx: RequesterCtx, endpoint_id: uuid.UUID
    ) -> CreateEndpointAutoScalingRuleAction:
        return CreateEndpointAutoScalingRuleAction(
            requester_ctx=requester_ctx,
            endpoint_id=endpoint_id,
            metric_source=AutoScalingMetricSource(self.metric_source),
            metric_name=self.metric_name,
            threshold=self.threshold,
            comparator=AutoScalingMetricComparator(self.comparator),
            step_size=self.step_size,
            cooldown_seconds=self.cooldown_seconds,
            min_replicas=self.min_replicas if self.min_replicas is not Undefined else None,
            max_replicas=self.max_replicas if self.max_replicas is not Undefined else None,
        )


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

    def to_action(
        self, requester_ctx: RequesterCtx, id: uuid.UUID
    ) -> ModifyEndpointAutoScalingRuleAction:
        def value_or_none(val: Any):
            return val if val is not Undefined else None

        return ModifyEndpointAutoScalingRuleAction(
            requester_ctx=requester_ctx,
            id=id,
            metric_source=OptionalState(
                "metric_source",
                define_state(self.metric_source),
                AutoScalingMetricSource(self.metric_source)
                if self.metric_source is not Undefined
                else None,
            ),
            metric_name=OptionalState(
                "metric_name",
                define_state(self.metric_name),
                value_or_none(self.metric_name),
            ),
            threshold=OptionalState(
                "threshold",
                define_state(self.threshold),
                value_or_none(self.threshold),
            ),
            comparator=OptionalState(
                "comparator",
                define_state(self.comparator),
                AutoScalingMetricComparator(self.comparator)
                if self.comparator is not Undefined
                else None,
            ),
            step_size=OptionalState(
                "step_size",
                define_state(self.step_size),
                value_or_none(self.step_size),
            ),
            cooldown_seconds=OptionalState(
                "cooldown_seconds",
                define_state(self.cooldown_seconds),
                value_or_none(self.cooldown_seconds),
            ),
            min_replicas=TriState(
                "min_replicas",
                define_state(self.min_replicas),
                value_or_none(self.min_replicas),
            ),
            max_replicas=TriState(
                "max_replicas",
                define_state(self.max_replicas),
                value_or_none(self.max_replicas),
            ),
        )


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
        graph_ctx: GraphQueryContext = info.context
        _, raw_endpoint_id = AsyncNode.resolve_global_id(info, endpoint)

        action = props.to_action(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=info.context.user["uuid"],
                user_role=info.context.user["role"],
                domain_name=info.context.user["domain_name"],
            ),
            endpoint_id=uuid.UUID(raw_endpoint_id),
        )

        result = await graph_ctx.processors.model_service.create_endpoint_auto_scaling_rule.wait_for_complete(
            action
        )

        return cls(
            ok=result.success,
            msg="Auto scaling rule created"
            if result.success
            else "Failed to create auto scaling rule",
            rule=EndpointAutoScalingRuleNode.from_dto(result.data) if result.data else None,
        )


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
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=graph_ctx.user["uuid"],
                user_role=graph_ctx.user["role"],
                domain_name=graph_ctx.user["domain_name"],
            ),
            id=UUID(rule_id),
        )

        result = await graph_ctx.processors.model_service.modify_endpoint_auto_scaling_rule.wait_for_complete(
            action
        )

        return cls(
            ok=result.success,
            msg="Auto scaling rule updated"
            if result.success
            else "Failed to update auto scaling rule",
            rule=EndpointAutoScalingRuleNode.from_dto(result.data) if result.data else None,
        )


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
        graph_ctx: GraphQueryContext = info.context

        action = DeleteEndpointAutoScalingRuleAction(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=graph_ctx.user["uuid"],
                user_role=graph_ctx.user["role"],
                domain_name=graph_ctx.user["domain_name"],
            ),
            id=UUID(rule_id),
        )

        result = await graph_ctx.processors.model_service.delete_endpoint_auto_scaling_rule.wait_for_complete(
            action
        )

        return cls(
            ok=result.success,
            msg="Auto scaling rule deleted"
            if result.success
            else "Failed to delete auto scaling rule",
        )

from __future__ import annotations

import datetime
import decimal
import uuid
from typing import TYPE_CHECKING, Any, Mapping, Optional, Self, Sequence, cast
from uuid import UUID

import graphene
import graphene_federation
import jwt
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined, UndefinedType
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    EndpointId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    RuleId,
    RuntimeVariant,
)
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.data.model_serving.modifier import (
    EndpointAutoScalingRuleModifier,
    EndpointModifier,
    ExtraMount,
    ImageRef,
)
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointData,
    RequesterCtx,
)
from ai.backend.manager.defs import SERVICE_MAX_RETRIES
from ai.backend.manager.models.gql_models.base import ImageRefType
from ai.backend.manager.models.gql_models.image import ImageNode
from ai.backend.manager.models.gql_models.vfolder import VirtualFolderNode
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.routing import RouteStatus, Routing
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.services.model_serving.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_serving.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_serving.actions.modify_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
)
from ai.backend.manager.services.model_serving.actions.modify_endpoint import ModifyEndpointAction
from ai.backend.manager.types import OptionalState, TriState

from ...errors.common import (
    GenericForbidden,
    ObjectNotFound,
)
from ...errors.service import (
    EndpointNotFound,
    EndpointTokenNotFound,
)
from ..base import (
    FilterExprArg,
    InferenceSessionError,
    Item,
    OrderExprArg,
    PaginatedList,
    generate_sql_info_for_gql_connection,
)
from ..endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..user import UserRole, UserRow

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


AutoScalingMetricSourceGQLEnum = graphene.Enum.from_enum(
    AutoScalingMetricSource,
    description="The source type to fetch metrics. Added in 25.1.0.",
)
AutoScalingMetricComparatorGQLEnum = graphene.Enum.from_enum(
    AutoScalingMetricComparator,
    description="The comparator used to compare the metric value with the threshold. Added in 25.1.0.",
)


@graphene_federation.key("id")
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
        self, requester_ctx: RequesterCtx, endpoint_id: EndpointId
    ) -> CreateEndpointAutoScalingRuleAction:
        return CreateEndpointAutoScalingRuleAction(
            requester_ctx=requester_ctx,
            endpoint_id=endpoint_id,
            creator=EndpointAutoScalingRuleCreator(
                metric_source=AutoScalingMetricSource(self.metric_source),
                metric_name=self.metric_name,
                threshold=self.threshold,
                comparator=AutoScalingMetricComparator(self.comparator),
                step_size=self.step_size,
                cooldown_seconds=self.cooldown_seconds,
                min_replicas=self.min_replicas if self.min_replicas is not Undefined else None,
                max_replicas=self.max_replicas if self.max_replicas is not Undefined else None,
            ),
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
        self, requester_ctx: RequesterCtx, id: RuleId
    ) -> ModifyEndpointAutoScalingRuleAction:
        def convert_to_decimal(
            value: Optional[str] | UndefinedType,
        ) -> decimal.Decimal | UndefinedType:
            if isinstance(value, UndefinedType):
                return value
            elif value is None:
                raise InvalidAPIParameters("Threshold cannot be None")

            try:
                return decimal.Decimal(value)
            except decimal.InvalidOperation:
                raise InvalidAPIParameters(f"Cannot convert {value} to Decimal")

        return ModifyEndpointAutoScalingRuleAction(
            requester_ctx=requester_ctx,
            id=id,
            modifier=EndpointAutoScalingRuleModifier(
                metric_source=OptionalState.from_graphql(
                    AutoScalingMetricSource(self.metric_source)
                    if self.metric_source is not Undefined
                    else Undefined,
                ),
                metric_name=OptionalState.from_graphql(
                    self.metric_name,
                ),
                threshold=OptionalState.from_graphql(
                    convert_to_decimal(self.threshold),
                ),
                comparator=OptionalState.from_graphql(
                    AutoScalingMetricComparator(self.comparator)
                    if self.comparator is not Undefined
                    else Undefined,
                ),
                step_size=OptionalState.from_graphql(
                    self.step_size,
                ),
                cooldown_seconds=OptionalState.from_graphql(
                    self.cooldown_seconds,
                ),
                min_replicas=TriState.from_graphql(
                    self.min_replicas,
                ),
                max_replicas=TriState.from_graphql(
                    self.max_replicas,
                ),
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
        if not raw_endpoint_id:
            raw_endpoint_id = endpoint
        try:
            _endpoint_id = EndpointId(UUID(raw_endpoint_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint")

        action = props.to_action(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=info.context.user["uuid"],
                user_role=info.context.user["role"],
                domain_name=info.context.user["domain_name"],
            ),
            endpoint_id=_endpoint_id,
        )

        result = await graph_ctx.processors.model_serving_auto_scaling.create_endpoint_auto_scaling_rule.wait_for_complete(
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
        if not rule_id:
            rule_id = id
        try:
            _rule_id = RuleId(UUID(rule_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=graph_ctx.user["uuid"],
                user_role=graph_ctx.user["role"],
                domain_name=graph_ctx.user["domain_name"],
            ),
            id=_rule_id,
        )

        result = await graph_ctx.processors.model_serving_auto_scaling.modify_endpoint_auto_scaling_rule.wait_for_complete(
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
        try:
            _rule_id = RuleId(UUID(rule_id))
        except ValueError:
            raise ObjectNotFound(object_name="Endpoint Autoscaling Rule")

        graph_ctx: GraphQueryContext = info.context

        action = DeleteEndpointAutoScalingRuleAction(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_id=graph_ctx.user["uuid"],
                user_role=graph_ctx.user["role"],
                domain_name=graph_ctx.user["domain_name"],
            ),
            id=_rule_id,
        )

        result = await graph_ctx.processors.model_serving_auto_scaling.delete_endpoint_auto_scaling_rule.wait_for_complete(
            action
        )

        return cls(
            ok=result.success,
            msg="Auto scaling rule deleted"
            if result.success
            else "Failed to delete auto scaling rule",
        )


class RuntimeVariantInfo(graphene.ObjectType):
    """Added in 24.03.5."""

    name = graphene.String()
    human_readable_name = graphene.String()

    @classmethod
    def from_enum(cls, enum: RuntimeVariant) -> Self:
        return cls(name=enum.value, human_readable_name=MODEL_SERVICE_RUNTIME_PROFILES[enum].name)


class Endpoint(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    endpoint_id = graphene.UUID()
    image = graphene.String(deprecation_reason="Deprecated since 23.09.9. use `image_object`")
    image_object = graphene.Field(ImageNode, description="Added in 23.09.9.")
    domain = graphene.String()
    project = graphene.String()
    resource_group = graphene.String()
    resource_slots = graphene.JSONString()
    url = graphene.String()
    model = graphene.UUID()
    model_definition_path = graphene.String(description="Added in 24.03.4.")
    model_vfolder = VirtualFolderNode()
    model_mount_destiation = graphene.String(
        deprecation_reason="Deprecated since 24.03.4; use `model_mount_destination` instead"
    )
    model_mount_destination = graphene.String(description="Added in 24.03.4.")
    extra_mounts = graphene.List(lambda: VirtualFolderNode, description="Added in 24.03.4.")
    created_user = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8. use `created_user_id`"
    )
    created_user_email = graphene.String(description="Added in 23.09.8.")
    created_user_id = graphene.UUID(description="Added in 23.09.8.")
    session_owner = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8. use `session_owner_id`"
    )
    session_owner_email = graphene.String(description="Added in 23.09.8.")
    session_owner_id = graphene.UUID(description="Added in 23.09.8.")
    tag = graphene.String()
    startup_command = graphene.String()
    bootstrap_script = graphene.String()
    callback_url = graphene.String()
    environ = graphene.JSONString()
    name = graphene.String()
    resource_opts = graphene.JSONString()
    replicas = graphene.Int(description="Added in 24.12.0. Replaces `desired_session_count`.")
    desired_session_count = graphene.Int(
        deprecation_reason="Deprecated since 24.12.0. Use `replicas` instead."
    )
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    open_to_public = graphene.Boolean()
    runtime_variant = graphene.Field(RuntimeVariantInfo, description="Added in 24.03.5.")

    created_at = GQLDateTime(required=True)
    destroyed_at = GQLDateTime()

    routings = graphene.List(Routing)
    retries = graphene.Int()
    status = graphene.String()

    lifecycle_stage = graphene.String()

    errors = graphene.List(graphene.NonNull(InferenceSessionError), required=True)

    live_stat = graphene.JSONString(description="Added in 24.12.0.")

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "name": ("endpoints_name", None),
        "endpoint_id": ("endpoints_id", None),
        "project": ("endpoints_project", None),
        "resource_group": ("endpoints_resource_group", None),
        "created_at": ("endpoints_created_at", dtparse),
        "retries": ("endpoints_retries", None),
        "replicas": ("endpoints_replicas", None),
        "destroyed_at": ("endpoints_destroyed_at", dtparse),
        "model": ("endpoints_model", None),
        "domain": ("endpoints_domain", None),
        "url": ("endpoints_url", None),
        "lifecycle_stage": ("endpoints_lifecycle_stage", EndpointLifecycle),
        "open_to_public": ("endpoints_open_to_public", None),
        "created_user_id": ("users_id", None),
        "created_user_email": ("users_email", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "name": ("endpoints_name", None),
        "endpoint_id": ("endpoints_id", None),
        "project": ("endpoints_project", None),
        "resource_group": ("endpoints_resource_group", None),
        "retries": ("endpoints_retries", None),
        "replicas": ("endpoints_replicas", None),
        "created_at": ("endpoints_created_at", None),
        "destroyed_at": ("endpoints_destroyed_at", None),
        "model": ("endpoints_model", None),
        "domain": ("endpoints_domain", None),
        "url": ("endpoints_url", None),
        "lifecycle_stage": ("endpoints_lifecycle_stage", None),
        "open_to_public": ("endpoints_open_to_public", None),
        "created_user_id": ("users_id", None),
        "created_user_email": ("users_email", None),
    }

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointRow,
    ) -> Self:
        creator = cast(Optional[UserRow], row.created_user_row)
        return cls(
            endpoint_id=row.id,
            # image="", # deprecated, row.image_object.name,
            image_object=ImageNode.from_row(ctx, row.image_row),
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots.to_json(),
            url=row.url,
            model=row.model,
            model_definition_path=row.model_definition_path,
            model_mount_destiation=row.model_mount_destination,
            model_mount_destination=row.model_mount_destination,
            created_user=row.created_user,
            created_user_id=row.created_user,
            created_user_email=creator.email if creator is not None else None,
            session_owner=row.session_owner,
            session_owner_id=row.session_owner,
            session_owner_email=row.session_owner_row.email,
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            name=row.name,
            resource_opts=row.resource_opts,
            replicas=row.replicas,
            desired_session_count=row.replicas,
            cluster_mode=row.cluster_mode,
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            routings=[await Routing.from_row(None, r, endpoint=row) for r in row.routings],
            lifecycle_stage=row.lifecycle_stage.name,
            runtime_variant=RuntimeVariantInfo.from_enum(row.runtime_variant),
        )

    @classmethod
    def from_dto(cls, ctx, dto: Optional[EndpointData]) -> Optional[Self]:
        if dto is None:
            return None
        return cls(
            endpoint_id=dto.id,
            image_object=ImageNode.from_row(ctx, ImageRow.from_optional_dataclass(dto.image)),
            domain=dto.domain,
            project=dto.project,
            resource_group=dto.resource_group,
            resource_slots=dto.resource_slots.to_json(),
            url=dto.url,
            model=dto.model,
            model_definition_path=dto.model_definition_path,
            model_mount_destiation=dto.model_mount_destination,
            model_mount_destination=dto.model_mount_destination,
            created_user=dto.created_user_id,
            created_user_id=dto.created_user_id,
            created_user_email=dto.created_user_email,
            session_owner=dto.session_owner_id,
            session_owner_id=dto.session_owner_id,
            session_owner_email=dto.session_owner_email,
            tag=dto.tag,
            startup_command=dto.startup_command,
            bootstrap_script=dto.bootstrap_script,
            callback_url=dto.callback_url,
            environ=dto.environ,
            name=dto.name,
            resource_opts=dto.resource_opts,
            replicas=dto.replicas,
            desired_session_count=dto.replicas,
            cluster_mode=dto.cluster_mode,
            cluster_size=dto.cluster_size,
            open_to_public=dto.open_to_public,
            created_at=dto.created_at,
            destroyed_at=dto.destroyed_at,
            retries=dto.retries,
            routings=[Routing.from_dto(r) for r in dto.routings] if dto.routings else None,
            lifecycle_stage=dto.lifecycle_stage,
            runtime_variant=RuntimeVariantInfo.from_enum(dto.runtime_variant),
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        project: UUID | None = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        filter: Optional[str] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(
            sa.join(
                EndpointRow,
                UserRow,
                EndpointRow.session_owner == UserRow.uuid,
                isouter=True,
            )
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)
        if filter is not None:
            filter_parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = filter_parser.append_filter(query, filter)

        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  #: GraphQueryContext,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: Optional[UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointRow)
            .select_from(
                sa.join(
                    EndpointRow,
                    UserRow,
                    EndpointRow.session_owner == UserRow.uuid,
                    isouter=True,
                )
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(EndpointRow.image_row).selectinload(ImageRow.aliases))
            .options(selectinload(EndpointRow.routings))
            .options(selectinload(EndpointRow.session_owner_row))
            .options(joinedload(EndpointRow.created_user_row))
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)

        if filter is not None:
            filter_parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = filter_parser.append_filter(query, filter)
        if order is not None:
            order_parser = QueryOrderParser(cls._queryorder_colmap)
            query = order_parser.append_ordering(query, order)
        else:
            query = query.order_by(sa.desc(EndpointRow.created_at))

        async with ctx.db.begin_readonly_session() as db_session:
            result = await db_session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: Optional[UUID] = None,
    ) -> Sequence[Self]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointRow.list(
                session,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
                load_image=True,
                load_created_user=True,
                load_session_owner=True,
            )
            return [await cls.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: UUID,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
        project: UUID | None = None,
    ) -> Self:
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointRow.get(
                    session,
                    endpoint_id=endpoint_id,
                    domain=domain_name,
                    user_uuid=user_uuid,
                    project=project,
                    load_image=True,
                    load_routes=True,
                    load_created_user=True,
                    load_session_owner=True,
                )
                return await cls.from_row(ctx, row)
        except NoResultFound:
            raise EndpointNotFound

    async def resolve_status(self, info: graphene.ResolveInfo) -> str:
        match self.lifecycle_stage:
            case EndpointLifecycle.DESTROYED.name:
                return EndpointStatus.DESTROYED
            case EndpointLifecycle.DESTROYING.name:
                return EndpointStatus.DESTROYING
            case _:
                if len(self.routings) == 0:
                    return EndpointStatus.READY
                elif self.retries > SERVICE_MAX_RETRIES:
                    return EndpointStatus.UNHEALTHY
                elif (spawned_service_count := len([r for r in self.routings])) > 0:
                    healthy_service_count = len([
                        r for r in self.routings if r.status == RouteStatus.HEALTHY.name
                    ])
                    if healthy_service_count == spawned_service_count:
                        return EndpointStatus.HEALTHY
                    unhealthy_service_count = len([
                        r for r in self.routings if r.status == RouteStatus.UNHEALTHY.name
                    ])
                    if unhealthy_service_count > 0:
                        return EndpointStatus.DEGRADED
                return EndpointStatus.PROVISIONING

    async def resolve_model_vfolder(self, info: graphene.ResolveInfo) -> VirtualFolderNode:
        if not self.model:
            raise ObjectNotFound(object_name="VFolder")

        ctx: GraphQueryContext = info.context

        async with ctx.db.begin_readonly_session() as sess:
            vfolder_row = await VFolderRow.get(sess, self.model, load_user=True, load_group=True)
            return VirtualFolderNode.from_row(info, vfolder_row)

    async def resolve_extra_mounts(self, info: graphene.ResolveInfo) -> Sequence[VirtualFolderNode]:
        if not self.endpoint_id:
            raise ObjectNotFound(object_name="Endpoint")

        ctx: GraphQueryContext = info.context

        async with ctx.db.begin_readonly_session() as sess:
            endpoint_row = await EndpointRow.get(sess, self.endpoint_id)
            extra_mount_folder_ids = [m.vfid.folder_id for m in endpoint_row.extra_mounts]
            query = (
                sa.select(VFolderRow)
                .where(VFolderRow.id.in_(extra_mount_folder_ids))
                .options(selectinload(VFolderRow.user_row))
                .options(selectinload(VFolderRow.group_row))
            )
            return [VirtualFolderNode.from_row(info, r) for r in (await sess.scalars(query))]

    async def resolve_errors(self, info: graphene.ResolveInfo) -> Any:
        error_routes = [r for r in self.routings if r.status == RouteStatus.FAILED_TO_START.name]
        errors = []
        for route in error_routes:
            if not route.error_data:
                continue
            match route.error_data["type"]:
                case "session_cancelled":
                    session_id = route.error_data["session_id"]
                case _:
                    session_id = None
            errors.append(
                InferenceSessionError(
                    session_id=session_id,
                    errors=[
                        InferenceSessionError.InferenceSessionErrorInfo(
                            src=e["src"], name=e["name"], repr=e["repr"]
                        )
                        for e in route.error_data["errors"]
                    ],
                )
            )

        return errors

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "EndpointStatistics.by_endpoint"
        )
        return await loader.load(self.endpoint_id)


class EndpointList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Endpoint, required=True)


class ExtraMountInput(graphene.InputObjectType):
    """Added in 24.03.4."""

    vfolder_id = graphene.String()
    mount_destination = graphene.String()
    type = graphene.String(
        description=f"Added in 24.03.4. Set bind type of this mount. Shoud be one of ({','.join([type_.value for type_ in MountTypes])}). Default is 'bind'."
    )
    permission = graphene.String(
        description=f"Added in 24.03.4. Set permission of this mount. Should be one of ({','.join([perm.value for perm in MountPermission])}). Default is null"
    )

    def to_action_field(self, info: graphene.ResolveInfo) -> ExtraMount:
        _, raw_vfolder_id = AsyncNode.resolve_global_id(info, self.vfolder_id)
        if not raw_vfolder_id:
            raw_vfolder_id = self.vfolder_id
        return ExtraMount(
            vfolder_id=OptionalState.from_graphql(UUID(raw_vfolder_id)),
            mount_destination=OptionalState.from_graphql(self.mount_destination),
            type=OptionalState.from_graphql(self.type),
            permission=OptionalState.from_graphql(self.permission),
        )


class ModifyEndpointInput(graphene.InputObjectType):
    resource_slots = graphene.JSONString()
    resource_opts = graphene.JSONString()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    replicas = graphene.Int(description="Added in 24.12.0. Replaces `desired_session_count`.")
    desired_session_count = graphene.Int(
        deprecation_reason="Deprecated since 24.12.0. Use `replicas` instead."
    )
    image = ImageRefType()
    name = graphene.String()
    resource_group = graphene.String()
    model_definition_path = graphene.String(
        description="Added in 24.03.4. Must be set to `/models` when choosing `runtime_variant` other than `CUSTOM` or `CMD`."
    )
    open_to_public = graphene.Boolean()
    extra_mounts = graphene.List(
        ExtraMountInput,
        description="Added in 24.03.4. MODEL type VFolders are not allowed to be attached to model service session with this option.",
    )
    environ = graphene.JSONString(description="Added in 24.03.5.")
    runtime_variant = graphene.String(description="Added in 24.03.5.")

    def to_action(
        self, requester_ctx: RequesterCtx, endpoint_id: uuid.UUID, info: graphene.ResolveInfo
    ) -> ModifyEndpointAction:
        def create_image_ref_from_input(graphene_image_input: ImageRefType) -> ImageRef:
            registry: OptionalState = OptionalState.nop()
            if (
                graphene_image_input.registry is not Undefined
                and graphene_image_input.registry is not None
            ):
                registry = OptionalState.update(graphene_image_input.registry)

            architecture: OptionalState = OptionalState.nop()
            if (
                graphene_image_input.architecture is not Undefined
                and graphene_image_input.architecture is not None
            ):
                architecture = OptionalState.update(graphene_image_input.architecture)

            return ImageRef(graphene_image_input.name, registry, architecture)

        def convert_runtime_variant(
            value: Optional[str] | UndefinedType,
        ) -> RuntimeVariant | UndefinedType:
            if isinstance(value, UndefinedType):
                return value
            elif value is None:
                raise InvalidAPIParameters("Runtime variant cannot be None")

            try:
                return RuntimeVariant(value)
            except KeyError:
                raise InvalidAPIParameters(f"Unsupported runtime {self.runtime_variant}")

        if self.desired_session_count is not Undefined and self.replicas is not Undefined:
            raise InvalidAPIParameters(
                "Cannot set both desired_session_count and replicas. Use replicas for future use."
            )

        def convert_extra_mounts(
            extra_mounts_gql: list[ExtraMountInput] | UndefinedType,
        ) -> list[ExtraMount] | UndefinedType:
            if isinstance(extra_mounts_gql, UndefinedType):
                return extra_mounts_gql
            elif extra_mounts_gql is None:
                raise InvalidAPIParameters("Extra mounts cannot be None")

            return [extra_mount.to_action_field(info) for extra_mount in extra_mounts_gql]

        return ModifyEndpointAction(
            requester_ctx=requester_ctx,
            endpoint_id=endpoint_id,
            modifier=EndpointModifier(
                resource_slots=OptionalState.from_graphql(
                    self.resource_slots
                    if (self.resource_slots is Undefined or self.resource_slots is None)
                    else ResourceSlot.from_user_input(self.resource_slots, None)
                ),
                resource_opts=TriState.from_graphql(self.resource_opts),
                cluster_mode=OptionalState.from_graphql(
                    self.cluster_mode
                    if (self.cluster_mode is Undefined or self.cluster_mode is None)
                    else ClusterMode(self.cluster_mode)
                ),
                cluster_size=OptionalState.from_graphql(self.cluster_size),
                replicas=OptionalState.from_graphql(self.replicas),
                desired_session_count=OptionalState.from_graphql(self.desired_session_count),
                image=TriState.from_graphql(
                    create_image_ref_from_input(self.image)
                    if self.image is not Undefined
                    else None,
                ),
                name=OptionalState.from_graphql(self.name),
                resource_group=OptionalState.from_graphql(self.resource_group),
                model_definition_path=TriState.from_graphql(self.model_definition_path),
                open_to_public=OptionalState.from_graphql(
                    self.open_to_public,
                ),
                extra_mounts=OptionalState.from_graphql(
                    self.extra_mounts
                    if (self.extra_mounts is Undefined or self.extra_mounts is None)
                    else convert_extra_mounts(self.extra_mounts),
                ),
                environ=TriState.from_graphql(
                    self.environ,
                ),
                runtime_variant=OptionalState.from_graphql(
                    convert_runtime_variant(self.runtime_variant),
                ),
            ),
        )


class ModifyEndpoint(graphene.Mutation):
    allowed_roles = (UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        endpoint_id = graphene.UUID(required=True)
        props = ModifyEndpointInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    endpoint = graphene.Field(lambda: Endpoint, required=False, description="Added in 23.09.8.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        endpoint_id: UUID,
        props: ModifyEndpointInput,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(
            requester_ctx=RequesterCtx(
                is_authorized=None,
                user_role=graph_ctx.user["role"],
                user_id=graph_ctx.user["uuid"],
                domain_name=graph_ctx.user["domain_name"],
            ),
            endpoint_id=endpoint_id,
            info=info,
        )

        result = await graph_ctx.processors.model_serving.modify_endpoint.wait_for_complete(action)

        return cls(
            ok=result.success,
            msg="success" if result.success else "failed",
            endpoint=Endpoint.from_dto(graph_ctx, result.data),
        )


@graphene_federation.key("token")
class EndpointToken(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    token = graphene.String(required=True)
    endpoint_id = graphene.UUID(required=True)
    domain = graphene.String(required=True)
    project = graphene.String(required=True)
    session_owner = graphene.UUID(required=True)

    created_at = GQLDateTime(required=True)
    valid_until = GQLDateTime()

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointTokenRow,
    ) -> Self:
        return cls(
            token=row.token,
            endpoint_id=row.endpoint,
            domain=row.domain,
            project=row.project,
            session_owner=row.session_owner,
            created_at=row.created_at,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: Optional[UUID] = None,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(EndpointTokenRow)
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        endpoint_id: Optional[UUID] = None,
        filter: str | None = None,
        order: str | None = None,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Sequence[Self]:
        query = (
            sa.select(EndpointTokenRow)
            .limit(limit)
            .offset(offset)
            .order_by(sa.desc(EndpointTokenRow.created_at))
        )
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        endpoint_id: UUID,
        *,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Sequence[Self]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointTokenRow.list(
                session,
                endpoint_id,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
            )
        return [await cls.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        token: str,
        *,
        project: Optional[UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[UUID] = None,
    ) -> Self:
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointTokenRow.get(
                    session, token, project=project, domain=domain_name, user_uuid=user_uuid
                )
        except NoResultFound:
            raise EndpointTokenNotFound
        return await cls.from_row(ctx, row)

    async def resolve_valid_until(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime.datetime | None:
        try:
            decoded = jwt.decode(
                self.token,
                algorithms=["HS256"],
                options={"verify_signature": False, "verify_exp": False},
            )
        except jwt.DecodeError:
            return None
        if "exp" not in decoded:
            return None
        return datetime.datetime.fromtimestamp(decoded["exp"], tz=tzutc())


class EndpointTokenList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(EndpointToken, required=True)

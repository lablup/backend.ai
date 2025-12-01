from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Self, cast

import graphene
import graphql
import sqlalchemy as sa
from graphql import Undefined, UndefinedType

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryData,
    ContainerRegistryModifier,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.gql_models.fields import ScopeField
from ai.backend.manager.models.rbac import (
    ContainerRegistryScope,
    ProjectScope,
    ScopeType,
    SystemScope,
)
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from ...defs import PASSWORD_PLACEHOLDER
from ..base import (
    BigInt,
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .group import GroupConnection, GroupNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext
from ..user import UserRole

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "AllowedGroups",
    "ContainerRegistryNode",
    "ContainerRegistryConnection",
    "ContainerRegistryScopeField",
    "ContainerRegistryTypeField",
    "CreateContainerRegistryNode",
    "ModifyContainerRegistryNode",
    "DeleteContainerRegistryNode",
)


class ContainerRegistryTypeField(graphene.Scalar):
    """Added in 24.09.0."""

    allowed_values = tuple(t.value for t in ContainerRegistryType)

    @staticmethod
    def serialize(val: ContainerRegistryType) -> str:
        return val.value

    @staticmethod
    def parse_literal(node, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ContainerRegistryType(node.value)

    @staticmethod
    def parse_value(value: str) -> ContainerRegistryType:
        return ContainerRegistryType(value)


class ContainerRegistryNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.09.0."

    row_id = graphene.UUID(
        description="Added in 24.09.0. The UUID type id of DB container_registries row."
    )
    name = graphene.String()
    url = graphene.String(required=True, description="Added in 24.09.0.")
    type = ContainerRegistryTypeField(required=True, description="Added in 24.09.0.")
    registry_name = graphene.String(required=True, description="Added in 24.09.0.")
    is_global = graphene.Boolean(description="Added in 24.09.0.")
    project = graphene.String(description="Added in 24.09.0.")
    username = graphene.String(description="Added in 24.09.0.")
    password = graphene.String(description="Added in 24.09.0.")
    ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
    extra = graphene.JSONString(description="Added in 24.09.3.")
    allowed_groups = PaginatedConnectionField(GroupConnection, description="Added in 25.3.0.")

    _queryfilter_fieldspec: dict[str, FieldSpecItem] = {
        "row_id": ("id", None),
        "registry_name": ("registry_name", None),
    }
    _queryorder_colmap: dict[str, OrderSpecItem] = {
        "row_id": ("id", None),
        "registry_name": ("registry_name", None),
    }

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> ContainerRegistryNode:
        graph_ctx: GraphQueryContext = info.context
        _, reg_id = AsyncNode.resolve_global_id(info, id)
        select_stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_row = cast(ContainerRegistryRow | None, await db_session.scalar(select_stmt))
            if reg_row is None:
                raise ValueError(f"Container registry not found (id: {reg_id})")
            return cls.from_row(graph_ctx, reg_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
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
            ContainerRegistryRow,
            ContainerRegistryRow.id,
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
        result = [cls.from_row(graph_ctx, cast(ContainerRegistryRow, row)) for row in reg_rows]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    def from_dataclass(cls, data: ContainerRegistryData) -> Self:
        return cls(
            id=data.id,  # auto-converted to Relay global ID
            row_id=data.id,
            url=data.url,
            type=data.type,
            registry_name=data.registry_name,
            project=data.project,
            username=data.username,
            password=PASSWORD_PLACEHOLDER if data.password is not None else None,
            ssl_verify=data.ssl_verify,
            is_global=data.is_global,
            extra=data.extra,
        )

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistryNode:
        return cls(
            id=row.id,  # auto-converted to Relay global ID
            row_id=row.id,
            url=row.url,
            type=row.type,
            registry_name=row.registry_name,
            project=row.project,
            username=row.username,
            password=PASSWORD_PLACEHOLDER if row.password is not None else None,
            ssl_verify=row.ssl_verify,
            is_global=row.is_global,
            extra=row.extra,
        )

    async def resolve_allowed_groups(
        self,
        info: graphene.ResolveInfo,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[GroupNode]:
        scope = SystemScope()

        if self.is_global:
            container_registry_scope = None
        else:
            container_registry_scope = ContainerRegistryScope.parse(f"container_registry:{self.id}")

        return await GroupNode.get_connection(
            info,
            scope,
            container_registry_scope,
            filter_expr=filter,
            order_expr=order,
            offset=offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )


class ContainerRegistryConnection(Connection):
    """Added in 25.3.0."""

    class Meta:
        node = ContainerRegistryNode
        description = "Added in 24.09.0."


class ContainerRegistryScopeField(graphene.Scalar):
    class Meta:
        description = "Added in 25.3.0."

    @staticmethod
    def serialize(val: ContainerRegistryScope) -> str:
        if isinstance(val, ContainerRegistryScope):
            return str(val)
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_value(value):
        if isinstance(value, str):
            try:
                return ContainerRegistryScope.parse(value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}")
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphql.language.ast.StringValueNode):
            try:
                return ContainerRegistryScope.parse(node.value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}")
        return None


class AllowedGroups(graphene.InputObjectType):
    """
    Added in 25.3.0.
    """

    add = graphene.List(
        graphene.String,
        default_value=[],
        description="List of group_ids to add associations. Added in 25.3.0.",
    )
    remove = graphene.List(
        graphene.String,
        default_value=[],
        description="List of group_ids to remove associations. Added in 25.3.0.",
    )


class CreateContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `CreateContainerRegistryNodeV2` instead
    """

    class Meta:
        description = "Added in 24.09.0."

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Arguments:
        url = graphene.String(required=True, description="Added in 24.09.0.")
        type = ContainerRegistryTypeField(
            required=True,
            description=f"Added in 24.09.0. Registry type. One of {ContainerRegistryTypeField.allowed_values}.",
        )
        registry_name = graphene.String(required=True, description="Added in 24.09.0.")
        is_global = graphene.Boolean(description="Added in 24.09.0.")
        project = graphene.String(description="Added in 24.09.0.")
        username = graphene.String(description="Added in 24.09.0.")
        password = graphene.String(description="Added in 24.09.0.")
        ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
        extra = graphene.JSONString(description="Added in 24.09.3.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        url: str,
        type: ContainerRegistryType,
        registry_name: str,
        project: str | UndefinedType = Undefined,
        is_global: bool | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict | UndefinedType = Undefined,
    ) -> CreateContainerRegistryNode:
        ctx: GraphQueryContext = info.context
        sanitized_project = cast(Optional[str], project if project is not Undefined else None)
        validator = ContainerRegistryValidator(
            ContainerRegistryValidatorArgs(
                url=url,
                type=type,
                project=sanitized_project,
            )
        )

        validator.validate()

        action = CreateContainerRegistryAction(
            creator=ContainerRegistryCreator(
                url=url,
                type=type,
                registry_name=registry_name,
                is_global=cast(Optional[bool], is_global if is_global is not Undefined else None),
                project=sanitized_project,
                username=cast(Optional[str], username if username is not Undefined else None),
                password=cast(Optional[str], password if password is not Undefined else None),
                ssl_verify=cast(
                    Optional[bool], ssl_verify if ssl_verify is not Undefined else None
                ),
                extra=cast(Optional[dict], extra if extra is not Undefined else None),
                allowed_groups=None,
            )
        )
        result = (
            await ctx.processors.container_registry.create_container_registry.wait_for_complete(
                action
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class ModifyContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `ModifyContainerRegistryNodeV2` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Meta:
        description = "Added in 24.09.0."

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 24.09.0.",
        )
        url = graphene.String(description="Added in 24.09.0.")
        type = ContainerRegistryTypeField(
            description=f"Registry type. One of {ContainerRegistryTypeField.allowed_values}. Added in 24.09.0."
        )
        registry_name = graphene.String(description="Added in 24.09.0.")
        is_global = graphene.Boolean(description="Added in 24.09.0.")
        project = graphene.String(description="Added in 24.09.0.")
        username = graphene.String(description="Added in 24.09.0.")
        password = graphene.String(description="Added in 24.09.0.")
        ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
        extra = graphene.JSONString(description="Added in 24.09.3.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        url: str | UndefinedType = Undefined,
        type: ContainerRegistryType | UndefinedType = Undefined,
        registry_name: str | UndefinedType = Undefined,
        is_global: bool | UndefinedType = Undefined,
        project: str | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict | UndefinedType = Undefined,
    ) -> ModifyContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        modifier = ContainerRegistryModifier(
            url=OptionalState.from_graphql(url),
            type=OptionalState.from_graphql(type),
            registry_name=OptionalState.from_graphql(registry_name),
            is_global=TriState.from_graphql(is_global),
            project=TriState.from_graphql(project),
            username=TriState.from_graphql(username),
            password=TriState.from_graphql(password),
            ssl_verify=TriState.from_graphql(ssl_verify),
            extra=TriState.from_graphql(extra),
            allowed_groups=TriState.nop(),
        )

        result = (
            await ctx.processors.container_registry.modify_container_registry.wait_for_complete(
                ModifyContainerRegistryAction(
                    id=reg_id,
                    modifier=modifier,
                )
            )
        )

        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class DeleteContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `DeleteContainerRegistryNodeV2` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Meta:
        description = "Added in 24.09.0."

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 24.09.0.",
        )

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
    ) -> DeleteContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)
        result = (
            await ctx.processors.container_registry.delete_container_registry.wait_for_complete(
                DeleteContainerRegistryAction(id=reg_id)
            )
        )

        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class CreateContainerRegistryQuota(graphene.Mutation):
    """Added in 25.3.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = BigInt(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int | float,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope():
                    await (
                        graph_ctx.services_ctx.per_project_container_registries_quota.create_quota(
                            scope_id, int(quota)
                        )
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))


class UpdateContainerRegistryQuota(graphene.Mutation):
    """Added in 25.3.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = BigInt(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int | float,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope(_):
                    await (
                        graph_ctx.services_ctx.per_project_container_registries_quota.update_quota(
                            scope_id, int(quota)
                        )
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))


class DeleteContainerRegistryQuota(graphene.Mutation):
    """Added in 25.3.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope(_):
                    await (
                        graph_ctx.services_ctx.per_project_container_registries_quota.delete_quota(
                            scope_id
                        )
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))

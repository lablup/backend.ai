from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Self, cast

import graphene
import graphql
import sqlalchemy as sa
from graphql import Undefined, UndefinedType

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.minilang import FieldSpecItem, OrderSpecItem
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.rbac import (
    ContainerRegistryScope,
    ProjectScope,
    ScopeType,
    SystemScope,
)
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import (
    BigInt,
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
    set_if_set,
)
from .fields import ScopeField
from .gql_relay import AsyncNode, Connection, ConnectionResolverResult
from .group import GroupConnection, GroupNode

if TYPE_CHECKING:
    from .schema import GraphQueryContext
from ai.backend.manager.models.user import UserRole

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
    # Legacy GraphQL classes (deprecated since 24.09.0)
    "CreateContainerRegistryInput",
    "ModifyContainerRegistryInput",
    "ContainerRegistryConfig",
    "ContainerRegistry",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)


class ContainerRegistryTypeField(graphene.Scalar):  # type: ignore[misc]
    """Added in 24.09.0."""

    allowed_values = tuple(t.value for t in ContainerRegistryType)

    @staticmethod
    def serialize(val: ContainerRegistryType) -> str:
        return val.value

    @staticmethod
    def parse_literal(
        node: graphql.language.ast.Node, _variables: dict[str, Any] | None = None
    ) -> ContainerRegistryType | None:
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ContainerRegistryType(node.value)
        return None

    @staticmethod
    def parse_value(value: str) -> ContainerRegistryType:
        return ContainerRegistryType(value)


class ContainerRegistryNode(graphene.ObjectType):  # type: ignore[misc]
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
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
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


class ContainerRegistryConnection(Connection):  # type: ignore[misc]
    """Added in 25.3.0."""

    class Meta:
        node = ContainerRegistryNode
        description = "Added in 24.09.0."


class ContainerRegistryScopeField(graphene.Scalar):  # type: ignore[misc]
    class Meta:
        description = "Added in 25.3.0."

    @staticmethod
    def serialize(val: ContainerRegistryScope) -> str:
        if isinstance(val, ContainerRegistryScope):
            return str(val)
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_value(value: str) -> ContainerRegistryScope:
        if isinstance(value, str):
            try:
                return ContainerRegistryScope.parse(value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}") from e
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_literal(node: graphql.language.ast.Node) -> ContainerRegistryScope | None:
        if isinstance(node, graphql.language.ast.StringValueNode):
            try:
                return ContainerRegistryScope.parse(node.value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}") from e
        return None


class AllowedGroups(graphene.InputObjectType):  # type: ignore[misc]
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


class CreateContainerRegistryNode(graphene.Mutation):  # type: ignore[misc]
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
            description=f"Added in 24.09.0. Container Registry type. One of {ContainerRegistryTypeField.allowed_values}.",
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
        root: Any,
        info: graphene.ResolveInfo,
        url: str,
        type: ContainerRegistryType,
        registry_name: str,
        is_global: bool | UndefinedType = Undefined,
        project: str | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict[str, Any] | UndefinedType = Undefined,
    ) -> CreateContainerRegistryNode:
        ctx: GraphQueryContext = info.context
        validator = ContainerRegistryValidator(
            ContainerRegistryValidatorArgs(
                url=url,
                type=type,
                project=cast(str | None, project if project is not Undefined else None),
            )
        )

        validator.validate()

        input_config: dict[str, Any] = {
            "registry_name": registry_name,
            "url": url,
            "type": type,
        }

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("project", project)
        _set_if_set("username", username)
        _set_if_set("password", password)
        _set_if_set("ssl_verify", ssl_verify)
        _set_if_set("is_global", is_global)
        _set_if_set("extra", extra)

        async with ctx.db.begin_session() as db_session:
            reg_row = ContainerRegistryRow(id=uuid.uuid4(), **input_config)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

            return cls(
                container_registry=ContainerRegistryNode.from_row(ctx, reg_row),
            )


class ModifyContainerRegistryNode(graphene.Mutation):  # type: ignore[misc]
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
            description=f"Container Registry type. One of {ContainerRegistryTypeField.allowed_values}. Added in 24.09.0."
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
        root: Any,
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
        extra: dict[str, Any] | UndefinedType = Undefined,
    ) -> ModifyContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        action = ModifyContainerRegistryAction(
            updater=Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.from_graphql(url),
                    type=OptionalState.from_graphql(type),
                    registry_name=OptionalState.from_graphql(registry_name),
                    is_global=TriState.from_graphql(is_global),
                    project=TriState.from_graphql(project),
                    username=TriState.from_graphql(username),
                    password=TriState.from_graphql(password),
                    ssl_verify=TriState.from_graphql(ssl_verify),
                    extra=TriState.from_graphql(extra),
                    allowed_groups=TriState.nop(),  # Not handled in this deprecated mutation
                ),
                pk_value=reg_id,
            )
        )

        # Execute action through processor
        result = (
            await ctx.processors.container_registry.modify_container_registry.wait_for_complete(
                action
            )
        )

        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class DeleteContainerRegistryNode(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ) -> DeleteContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        result = (
            await ctx.processors.container_registry.delete_container_registry.wait_for_complete(
                DeleteContainerRegistryAction(
                    purger=Purger(row_class=ContainerRegistryRow, pk_value=reg_id)
                )
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class CreateContainerRegistryQuota(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


class UpdateContainerRegistryQuota(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


class DeleteContainerRegistryQuota(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


# ================================================================================
# Legacy GraphQL classes (deprecated since 24.09.0)
# Moved from models/container_registry/row.py
# ================================================================================


class CreateContainerRegistryInput(graphene.InputObjectType):  # type: ignore[misc]
    """
    Deprecated since 24.09.0.
    """

    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ModifyContainerRegistryInput(graphene.InputObjectType):  # type: ignore[misc]
    """
    Deprecated since 24.09.0.
    """

    url = graphene.String()
    type = graphene.String()
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ContainerRegistryConfig(graphene.ObjectType):  # type: ignore[misc]
    """
    Deprecated since 24.09.0.
    """

    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ContainerRegistry(graphene.ObjectType):  # type: ignore[misc]
    """
    Deprecated since 24.09.0. use `ContainerRegistryNode` instead
    """

    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    class Meta:
        interfaces = (AsyncNode,)

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistry:
        return cls(
            id=row.id,  # auto-converted to Relay global ID
            hostname=row.registry_name,
            config=ContainerRegistryConfig(
                url=row.url,
                type=str(row.type),
                project=[row.project],
                username=row.username,
                password=PASSWORD_PLACEHOLDER if row.password is not None else None,
                ssl_verify=row.ssl_verify,
                is_global=row.is_global,
            ),
        )

    @classmethod
    async def load_by_hostname(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        async with ctx.db.begin_readonly_session() as session:
            return cls.from_row(
                ctx,
                (
                    await ContainerRegistryRow.list_by_registry_name(
                        session,
                        hostname,
                    )
                )[0],
            )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
    ) -> Sequence[ContainerRegistry]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await session.scalars(sa.select(ContainerRegistryRow))
            return [cls.from_row(ctx, row) for row in rows]


class CreateContainerRegistry(graphene.Mutation):  # type: ignore[misc]
    """
    Deprecated since 24.09.0. use `CreateContainerRegistryNode` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
        props = CreateContainerRegistryInput(required=True)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        hostname: str,
        props: CreateContainerRegistryInput,
    ) -> CreateContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {
            "registry_name": hostname,
            "url": props.url,
            "type": ContainerRegistryType(props.type),
        }

        if props.project:
            input_config["project"] = props.project[0]

        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")
        set_if_set(props, input_config, "is_global")

        async with ctx.db.begin_session() as db_session:
            reg_row = ContainerRegistryRow(id=uuid.uuid4(), **input_config)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

            return cls(
                container_registry=ContainerRegistry.from_row(ctx, reg_row),
            )


class ModifyContainerRegistry(graphene.Mutation):  # type: ignore[misc]
    """
    Deprecated since 24.09.0. use `ModifyContainerRegistryNode` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
        props = ModifyContainerRegistryInput(required=True)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        hostname: str,
        props: ModifyContainerRegistryInput,
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {
            "registry_name": hostname,
        }

        if props.project:
            input_config["project"] = props.project[0]

        if props.type:
            input_config["type"] = ContainerRegistryType(props.type)

        set_if_set(props, input_config, "url")
        set_if_set(props, input_config, "is_global")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")

        async with ctx.db.begin_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == hostname
            )
            reg_row = await session.scalar(stmt)
            if reg_row is None:
                raise ValueError(f"ContainerRegistry not found (hostname: {hostname})")

            for field, val in input_config.items():
                setattr(reg_row, field, val)

            return cls(container_registry=ContainerRegistry.from_row(ctx, reg_row))


class DeleteContainerRegistry(graphene.Mutation):  # type: ignore[misc]
    """
    Deprecated since 24.09.0. use `DeleteContainerRegistryNode` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        hostname: str,
    ) -> DeleteContainerRegistry:
        ctx: GraphQueryContext = info.context
        container_registry = await ContainerRegistry.load_by_hostname(ctx, hostname)
        async with ctx.db.begin_session() as session:
            stmt = sa.delete(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == hostname
            )
            await session.execute(stmt)
        return cls(container_registry=container_registry)

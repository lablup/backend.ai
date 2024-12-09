from __future__ import annotations

import enum
import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Mapping, MutableMapping, cast

import graphene
import graphql
import sqlalchemy as sa
import yarl
from graphql import Undefined, UndefinedType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, relationship
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.exception import UnknownImageRegistry
from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import (
    Base,
    FilterExprArg,
    IDColumn,
    OrderExprArg,
    StrEnumType,
    generate_sql_info_for_gql_connection,
    set_if_set,
)
from .gql_relay import AsyncNode, Connection, ConnectionResolverResult
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "ContainerRegistry",
    "ContainerRegistryRow",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)


class ContainerRegistryType(enum.StrEnum):
    DOCKER = "docker"
    HARBOR = "harbor"
    HARBOR2 = "harbor2"
    GITHUB = "github"
    GITLAB = "gitlab"
    ECR = "ecr"
    ECR_PUB = "ecr-public"
    LOCAL = "local"


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"
    id = IDColumn()
    url = sa.Column("url", sa.String(length=512), index=True, nullable=False)
    registry_name = sa.Column("registry_name", sa.String(length=50), index=True, nullable=False)
    type = sa.Column(
        "type",
        StrEnumType(ContainerRegistryType),
        default=ContainerRegistryType.DOCKER,
        server_default=ContainerRegistryType.DOCKER,
        nullable=False,
        index=True,
    )
    project = sa.Column("project", sa.String(length=255), index=True, nullable=True)
    username = sa.Column("username", sa.String(length=255), nullable=True)
    password = sa.Column("password", sa.String, nullable=True)
    ssl_verify = sa.Column(
        "ssl_verify", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    is_global = sa.Column(
        "is_global", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    extra = sa.Column("extra", sa.JSON, nullable=True, default=None)

    image_rows = relationship(
        "ImageRow",
        back_populates="registry_row",
        primaryjoin="ContainerRegistryRow.id == foreign(ImageRow.registry_id)",
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        id: str | uuid.UUID,
    ) -> ContainerRegistryRow:
        query = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == id)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list_by_registry_name(
        cls,
        session: AsyncSession,
        registry_name: str,
    ) -> Sequence[ContainerRegistryRow]:
        query = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name
        )
        result = await session.execute(query)
        rows = result.scalars().all()
        if not rows:
            raise NoResultFound
        return rows

    @classmethod
    async def get_container_registry_info(
        cls, session: AsyncSession, registry_id: uuid.UUID
    ) -> tuple[yarl.URL, dict]:
        query_stmt = (
            sa.select(ContainerRegistryRow)
            .where(ContainerRegistryRow.id == registry_id)
            .options(
                load_only(
                    ContainerRegistryRow.url,
                    ContainerRegistryRow.username,
                    ContainerRegistryRow.password,
                )
            )
        )
        registry_row = cast(ContainerRegistryRow | None, await session.scalar(query_stmt))
        if registry_row is None:
            raise UnknownImageRegistry(registry_id)
        url = registry_row.url
        username = registry_row.username
        password = registry_row.password
        creds = {"username": username, "password": password}

        return yarl.URL(url), creds

    @classmethod
    async def get_known_container_registries(
        cls,
        session: AsyncSession,
    ) -> Mapping[str, Mapping[str, yarl.URL]]:
        query_stmt = sa.select(ContainerRegistryRow).options(
            load_only(
                ContainerRegistryRow.project,
                ContainerRegistryRow.registry_name,
                ContainerRegistryRow.url,
            )
        )
        registries = cast(list[ContainerRegistryRow], (await session.scalars(query_stmt)).all())
        result: MutableMapping[str, MutableMapping[str, yarl.URL]] = {}
        for registry_row in registries:
            project = registry_row.project
            registry_name = registry_row.registry_name
            url = registry_row.url
            if project not in result:
                result[project] = {}
            result[project][registry_name] = yarl.URL(url)
        return result


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


# Legacy
class CreateContainerRegistryInput(graphene.InputObjectType):
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


# Legacy
class ModifyContainerRegistryInput(graphene.InputObjectType):
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


# Legacy
class ContainerRegistryConfig(graphene.ObjectType):
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


# Legacy
class ContainerRegistry(graphene.ObjectType):
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


class ContainerRegistryConnection(Connection):
    """Added in 24.09.0."""

    class Meta:
        node = ContainerRegistryNode
        description = "Added in 24.09.0."


class CreateContainerRegistryNode(graphene.Mutation):
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
        is_global: bool | UndefinedType = Undefined,
        project: str | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict | UndefinedType = Undefined,
    ) -> CreateContainerRegistryNode:
        ctx: GraphQueryContext = info.context

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
            reg_row = ContainerRegistryRow(**input_config)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

            return cls(
                container_registry=ContainerRegistryNode.from_row(ctx, reg_row),
            )


class ModifyContainerRegistryNode(graphene.Mutation):
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

        input_config: dict[str, Any] = {}

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("url", url)
        _set_if_set("type", type)
        _set_if_set("registry_name", registry_name)
        _set_if_set("username", username)
        _set_if_set("password", password)
        _set_if_set("project", project)
        _set_if_set("ssl_verify", ssl_verify)
        _set_if_set("is_global", is_global)
        _set_if_set("extra", extra)

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        async with ctx.db.begin_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            reg_row = await session.scalar(stmt)
            if reg_row is None:
                raise ValueError(f"ContainerRegistry not found (id: {reg_id})")
            for field, val in input_config.items():
                setattr(reg_row, field, val)

            return cls(container_registry=ContainerRegistryNode.from_row(ctx, reg_row))


class DeleteContainerRegistryNode(graphene.Mutation):
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
        async with ctx.db.begin_session() as db_session:
            reg_row = await ContainerRegistryRow.get(db_session, reg_id)
            reg_row = await db_session.scalar(
                sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            )
            if reg_row is None:
                raise ValueError(f"Container registry not found (id:{reg_id})")
            container_registry = ContainerRegistryNode.from_row(ctx, reg_row)
            await db_session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            )

        return cls(container_registry=container_registry)


# Legacy mutations
class CreateContainerRegistry(graphene.Mutation):
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
        cls, root, info: graphene.ResolveInfo, hostname: str, props: CreateContainerRegistryInput
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
            reg_row = ContainerRegistryRow(**input_config)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

            return cls(
                container_registry=ContainerRegistry.from_row(ctx, reg_row),
            )


# Legacy mutations
class ModifyContainerRegistry(graphene.Mutation):
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
        root,
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


# Legacy mutations
class DeleteContainerRegistry(graphene.Mutation):
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
        root,
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

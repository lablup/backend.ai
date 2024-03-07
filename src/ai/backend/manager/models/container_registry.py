from __future__ import annotations

import enum
import logging
import uuid
from typing import TYPE_CHECKING, Any, Sequence

import graphene
import graphql
import sqlalchemy as sa
from graphene.types import Scalar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import (
    Base,
    FilterExprArg,
    IDColumn,
    OrderExprArg,
    StrEnumType,
    generate_sql_info_for_gql_connection,
    privileged_mutation,
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
    LOCAL = "local"


class ContainerRegistryTypeField(Scalar):
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


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"
    id = IDColumn()
    url = sa.Column("url", sa.String(length=512), index=True)
    registry_name = sa.Column("registry_name", sa.String(length=50), index=True)
    type = sa.Column(
        "type",
        StrEnumType(ContainerRegistryType),
        default=ContainerRegistryType.DOCKER,
        server_default=ContainerRegistryType.DOCKER,
        nullable=False,
        index=True,
    )
    project = sa.Column("project", sa.String(length=255), nullable=True)  # harbor only
    username = sa.Column("username", sa.String(length=255), nullable=True)
    password = sa.Column("password", sa.String(length=255), nullable=True)
    ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)
    is_global = sa.Column("is_global", sa.Boolean, server_default=sa.text("true"), index=True)

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


class CreateContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    type = ContainerRegistryTypeField(required=True)
    registry_name = graphene.String(required=True)
    is_global = graphene.Boolean()
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String()
    type = ContainerRegistryTypeField()
    registry_name = graphene.String()
    is_global = graphene.Boolean()
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    type = ContainerRegistryTypeField(required=True)
    registry_name = graphene.String(required=True)
    is_global = graphene.Boolean()
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistry(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    config = graphene.Field(ContainerRegistryConfig)

    _queryfilter_fieldspec: dict[str, FieldSpecItem] = {
        "id": ("id", None),
        "registry_name": ("registry_name", None),
    }

    _queryorder_colmap: dict[str, OrderSpecItem] = {
        "id": ("id", None),
        "registry_name": ("registry_name", None),
    }

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> ContainerRegistry:
        graph_ctx: GraphQueryContext = info.context

        _, reg_id = AsyncNode.resolve_global_id(info, id)
        select_stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_row = await db_session.scalar(select_stmt)
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
            conditions,
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
        cnt_query = sa.select(sa.func.count()).select_from(ContainerRegistryRow)
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(graph_ctx, row) for row in reg_rows]

            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistry:
        return cls(
            id=row.id,
            config=ContainerRegistryConfig(
                url=row.url,
                type=row.type,
                registry_name=row.registry_name,
                project=row.project,
                username=row.username,
                password=PASSWORD_PLACEHOLDER if row.password is not None else None,
                ssl_verify=row.ssl_verify,
                is_global=row.is_global,
            ),
        )

    @classmethod
    async def load(cls, ctx: GraphQueryContext, id: str | uuid.UUID) -> ContainerRegistry:
        async with ctx.db.begin_readonly_session() as session:
            return cls.from_row(
                ctx,
                await ContainerRegistryRow.get(
                    session,
                    id,
                ),
            )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
    ) -> Sequence[ContainerRegistry]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await session.execute(sa.select(ContainerRegistryRow))
            return [cls.from_row(ctx, row) for row in rows]

    @classmethod
    async def list_by_registry_name(
        cls,
        ctx: GraphQueryContext,
        registry_name: str,
    ) -> Sequence[ContainerRegistry]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await ContainerRegistryRow.list_by_registry_name(session, registry_name)
            return [cls.from_row(ctx, row) for row in rows]


class ContainerRegistryConnection(Connection):
    class Meta:
        node = ContainerRegistry


class CreateContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    id = graphene.UUID(required=True)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        props = CreateContainerRegistryInput(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls, root, info: graphene.ResolveInfo, props: CreateContainerRegistryInput
    ) -> CreateContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {
            "registry_name": props.registry_name,
            "url": props.url,
            "type": ContainerRegistryType(props.type),
        }

        set_if_set(props, input_config, "project")
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
                id=reg_row.id,
                container_registry=ContainerRegistry.from_row(ctx, reg_row),
            )


class ModifyContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        id = graphene.UUID(required=True)
        props = ModifyContainerRegistryInput(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
        props: ModifyContainerRegistryInput,
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {}

        set_if_set(props, input_config, "url")
        set_if_set(props, input_config, "type")
        set_if_set(props, input_config, "registry_name")
        set_if_set(props, input_config, "is_global")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "ssl_verify")

        async with ctx.db.begin_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == id)
            reg_row = await session.scalar(stmt)
            if reg_row is None:
                raise ValueError(f"ContainerRegistry not found (id: {id})")
            for field, val in input_config.items():
                setattr(reg_row, field, val)

            return cls(container_registry=ContainerRegistry.from_row(ctx, reg_row))


class DeleteContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        id = graphene.UUID(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: uuid.UUID,
    ) -> DeleteContainerRegistry:
        ctx: GraphQueryContext = info.context
        container_registry = await ContainerRegistry.load(ctx, id)
        async with ctx.db.begin_session() as session:
            await session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == id)
            )

        return cls(container_registry=container_registry)

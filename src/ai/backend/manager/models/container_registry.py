from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import (
    Base,
    FilterExprArg,
    IDColumn,
    OrderExprArg,
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


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"
    id = IDColumn()
    url = sa.Column("url", sa.String(length=255), index=True)
    registry_name = sa.Column("registry_name", sa.String(length=50), index=True)
    type = sa.Column(
        "type",
        sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
        default="docker",
        index=True,
    )
    project = sa.Column("project", sa.String(length=255), nullable=True)  # harbor only
    username = sa.Column("username", sa.String(length=255), nullable=True)
    password = sa.Column("password", sa.String(length=255), nullable=True)
    ssl_verify = sa.Column("ssl_verify", sa.Boolean, server_default=sa.text("true"), index=True)

    def __init__(
        self,
        url: str,
        registry_name: str,
        type: str,
        ssl_verify: bool,
        project: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.registry_name = registry_name
        self.url = url
        self.type = type
        self.project = project
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        id: str,
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
    type = graphene.String(required=True)
    registry_name = graphene.String(required=True)
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String()
    type = graphene.String()
    registry_name = graphene.String()
    project = graphene.String()
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    registry_name = graphene.String(required=True)
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
            ),
        )

    @classmethod
    async def load(cls, ctx: GraphQueryContext, id: str) -> ContainerRegistry:
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
    id = graphene.String(required=True)
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
            "type": props.type,
        }

        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")

        async with ctx.db.begin_session() as session:
            result = await session.execute(
                sa.insert(ContainerRegistryRow)
                .values(input_config)
                .returning(ContainerRegistryRow.id)
            )
            inserted_item_id = result.scalar()

            return cls(
                id=inserted_item_id,
                container_registry=ContainerRegistry.from_row(
                    ctx, await ContainerRegistryRow.get(session, inserted_item_id)
                ),
            )


class ModifyContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        id = graphene.String(required=True)
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
        id: graphene.String,
        props: ModifyContainerRegistryInput,
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: Dict[str, Any] = {}

        set_if_set(props, input_config, "url")
        set_if_set(props, input_config, "type")
        set_if_set(props, input_config, "registry_name")
        set_if_set(props, input_config, "project")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")

        async with ctx.db.begin_session() as session:
            _, reg_id = AsyncNode.resolve_global_id(info, id)

            query = (
                sa.update(ContainerRegistryRow)
                .values(input_config)
                .where(ContainerRegistryRow.id == reg_id)
            )

            await session.execute(query)

            return cls(
                container_registry=ContainerRegistry.from_row(
                    ctx, await ContainerRegistryRow.get(session, reg_id)
                )
            )


class DeleteContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        id = graphene.String(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: graphene.String,
    ) -> DeleteContainerRegistry:
        ctx: GraphQueryContext = info.context
        _, reg_id = AsyncNode.resolve_global_id(info, id)
        container_registry = await ContainerRegistry.load(ctx, reg_id)
        async with ctx.db.begin_session() as session:
            await session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            )

        return cls(container_registry=container_registry)

from __future__ import annotations

import logging
import uuid
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
from .gql_relay import AsyncNode, ConnectionResolverResult
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "ContainerRegistryRow",
    "ContainerRegistry",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"
    id = IDColumn()
    url = sa.Column("url", sa.String(length=255), index=True)
    hostname = sa.Column("hostname", sa.String(length=50), index=True)
    type = sa.Column(
        "type",
        sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
        default="docker",
        index=True,
    )
    project = sa.Column("project", sa.Text, nullable=True)  # harbor only
    username = sa.Column("username", sa.String(length=255), nullable=True)
    password = sa.Column("password", sa.String(length=255), nullable=True)
    ssl_verify = sa.Column("ssl_verify", sa.Boolean, default=True, index=True)

    def __init__(
        self,
        hostname: str,
        url: str,
        type: str,
        ssl_verify: bool,
        username: Optional[str] = None,
        password: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        self.hostname = hostname
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
        id: uuid.UUID,
    ) -> ContainerRegistryRow:
        query = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == id)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def get_by_hostname(
        cls,
        session: AsyncSession,
        hostname: str,
    ) -> ContainerRegistryRow:
        query = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.hostname == hostname)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row


class CreateContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String()
    type = graphene.String()
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()


class ContainerRegistry(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> ContainerRegistry:
        graph_ctx: GraphQueryContext = info.context

        _, reg_id = AsyncNode.resolve_global_id(info, id)
        select_stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_row = await db_session.scalar(select_stmt)
            return cls.from_row(graph_ctx, reg_row)

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistry:
        return cls(
            id=row.id,
            hostname=row.hostname,
            config=ContainerRegistryConfig(
                url=row.url,
                type=row.type,
                project=row.project.split(",") if row.project is not None else [],
                username=row.username,
                password=PASSWORD_PLACEHOLDER if row.password is not None else None,
                ssl_verify=row.ssl_verify,
            ),
        )

    _queryfilter_fieldspec: dict[str, FieldSpecItem] = {
        "id": ("id", None),
        "hostname": ("hostname", None),
    }

    _queryorder_colmap: dict[str, OrderSpecItem] = {
        "id": ("id", None),
        "hostname": ("hostname", None),
    }

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
            ContainerRegistry,
            ContainerRegistry.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        cnt_query = sa.select(sa.func.count()).select_from(ContainerRegistry)
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(graph_ctx, row) for row in reg_rows]

            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
    ) -> Sequence[ContainerRegistry]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await session.execute(sa.select(ContainerRegistryRow))
            return [cls.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_registry(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        async with ctx.db.begin_readonly_session() as session:
            return cls.from_row(
                ctx,
                await ContainerRegistryRow.get_by_hostname(
                    session,
                    hostname,
                ),
            )


class CreateContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
        props = CreateContainerRegistryInput(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls, root, info: graphene.ResolveInfo, hostname: str, props: CreateContainerRegistryInput
    ) -> CreateContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: Dict[str, Any] = {"hostname": hostname, "url": props.url, "type": props.type}

        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")
        set_if_set(props, input_config, "project")

        if "project" in input_config.keys():
            input_config["project"] = ",".join(input_config["project"])

        async with ctx.db.begin_session() as session:
            query = sa.insert(ContainerRegistryRow).values(input_config)
            await session.execute(query)

        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        return cls(container_registry=container_registry)


class ModifyContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)
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
        hostname: str,
        props: ModifyContainerRegistryInput,
    ) -> ModifyContainerRegistry:
        ctx: GraphQueryContext = info.context

        input_config: Dict[str, Any] = {}

        set_if_set(props, input_config, "url")
        set_if_set(props, input_config, "type")
        set_if_set(props, input_config, "username")
        set_if_set(props, input_config, "password")
        set_if_set(props, input_config, "ssl_verify")
        set_if_set(props, input_config, "project")

        if "project" in input_config.keys():
            input_config["project"] = ",".join(input_config["project"])

        async with ctx.db.begin_session() as session:
            query = (
                sa.update(ContainerRegistryRow)
                .values(input_config)
                .where(ContainerRegistryRow.hostname == hostname)
            )

            await session.execute(query)

        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        return cls(container_registry=container_registry)


class DeleteContainerRegistry(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistry)

    class Arguments:
        hostname = graphene.String(required=True)

    @classmethod
    @privileged_mutation(
        UserRole.SUPERADMIN,
        lambda id, **kwargs: (None, id),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        hostname: str,
    ) -> DeleteContainerRegistry:
        ctx: GraphQueryContext = info.context
        container_registry = await ContainerRegistry.load_registry(ctx, hostname)
        async with ctx.db.begin_session() as session:
            await session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.hostname == hostname)
            )

        return cls(container_registry=container_registry)

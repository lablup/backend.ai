from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Optional, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import Base, IDColumn, mapper_registry, privileged_mutation
from .gql_relay import AsyncNode
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "container_registries",
    "ContainerRegistryRow",
    "ContainerRegistry",
    "CreateContainerRegistry",
    "ModifyContainerRegistry",
    "DeleteContainerRegistry",
)

container_registries = sa.Table(
    "container_registries",
    mapper_registry.metadata,
    IDColumn(),
    sa.Column("url", sa.String(length=255), index=True),
    sa.Column("hostname", sa.String(length=50), index=True),
    sa.Column(
        "type",
        sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
        default="docker",
        index=True,
    ),
    sa.Column("project", sa.Text, nullable=True),  # harbor only
    sa.Column("username", sa.String(length=255), nullable=True),
    sa.Column("password", sa.String(length=255), nullable=True),
    sa.Column("ssl_verify", sa.Boolean, default=True, index=True),
)


class ContainerRegistryRow(Base):
    __table__ = container_registries
    # __tablename__ = "container_registries"
    # id = IDColumn()
    # url = sa.Column("url", sa.String(length=255), index=True)
    # hostname = sa.Column("hostname", sa.String(length=50), index=True)
    # type = sa.Column(
    #     "type",
    #     sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
    #     default="docker",
    #     index=True,
    # )
    # project = sa.Column("project", sa.Text, nullable=True)  # harbor only
    # username = sa.Column("username", sa.String(length=255), nullable=True)
    # password = sa.Column("password", sa.String(length=255), nullable=True)
    # ssl_verify = sa.Column("ssl_verify", sa.Boolean, default=True, index=True)

    def __init__(
        self,
        id: uuid.UUID,
        hostname: str,
        url: str,
        type: str,
        ssl_verify: bool,
        username: Optional[str] = None,
        password: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        self.id = id
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
    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    class Meta:
        interfaces = (AsyncNode,)

    # TODO: `get_node()` should be implemented to query a scalar object directly by ID
    #       (https://docs.graphene-python.org/en/latest/relay/nodes/#nodes)
    # @classmethod
    # def get_node(cls, info: graphene.ResolveInfo, id):
    #     raise NotImplementedError

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> ContainerRegistry:
        return cls(
            id=row["id"],
            hostname=row["name"],
            config=ContainerRegistryConfig(
                url=row["url"],
                type=row["type"],
                project=row["project"],
                username=row["username"],
                password=PASSWORD_PLACEHOLDER if row["password"] is not None else None,
                ssl_verify=row["ssl_verify"],
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
        data = {
            "hostname": hostname,
            "url": props.url,
            "type": props.type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
            "ssl_verify": props.ssl_verify,
        }

        async with ctx.db.begin_session() as session:
            await session.execute(sa.insert(container_registries).values(data))

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
        data = {
            "hostname": hostname,
            "url": props.url,
            "type": props.type,
            "project": props.project,
            "username": props.username,
            "password": props.password,
            "ssl_verify": props.ssl_verify,
        }

        async with ctx.db.begin_session() as session:
            await session.execute(
                sa.update(container_registries)
                .where(ContainerRegistryRow.hostname == hostname)
                .values(data)
            )
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
                sa.delete(container_registries).where(ContainerRegistryRow.hostname == hostname)
            )

        return cls(container_registry=container_registry)

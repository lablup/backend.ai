from __future__ import annotations

import enum
import logging
import uuid
from typing import TYPE_CHECKING, Any, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import (
    Base,
    IDColumn,
    StrEnumType,
    privileged_mutation,
    set_if_set,
)
from .gql_relay import AsyncNode
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
    project = sa.Column("project", sa.String(length=255), index=True, nullable=False)
    username = sa.Column("username", sa.String(length=255), nullable=True)
    password = sa.Column("password", sa.String, nullable=True)
    ssl_verify = sa.Column(
        "ssl_verify", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    is_global = sa.Column(
        "is_global", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
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

    # TODO: Remove the following function assuming the registry_name is unique.
    @classmethod
    async def get_by_hostname(
        cls,
        session: AsyncSession,
        hostname: str,
    ) -> ContainerRegistryRow:
        query = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == hostname
        )
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
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ModifyContainerRegistryInput(graphene.InputObjectType):
    url = graphene.String()
    type = graphene.String()
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ContainerRegistryConfig(graphene.ObjectType):
    url = graphene.String(required=True)
    type = graphene.String(required=True)
    project = graphene.List(graphene.String)
    username = graphene.String()
    password = graphene.String()
    ssl_verify = graphene.Boolean()
    is_global = graphene.Boolean(description="Added in 24.09.0.")


class ContainerRegistry(graphene.ObjectType):
    hostname = graphene.String()
    config = graphene.Field(ContainerRegistryConfig)

    class Meta:
        interfaces = (AsyncNode,)

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistry:
        return cls(
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

    # TODO: Remove the following function assuming the registry_name is unique.
    @classmethod
    async def load_by_hostname(cls, ctx: GraphQueryContext, hostname: str) -> ContainerRegistry:
        async with ctx.db.begin_readonly_session() as session:
            return cls.from_row(
                ctx,
                await ContainerRegistryRow.get_by_hostname(
                    session,
                    hostname,
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
        container_registry = await ContainerRegistry.load_by_hostname(ctx, hostname)
        async with ctx.db.begin_session() as session:
            stmt = sa.delete(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == hostname
            )
            await session.execute(stmt)
        return cls(container_registry=container_registry)

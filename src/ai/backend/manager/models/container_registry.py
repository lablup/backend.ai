from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Mapping, MutableMapping, cast

import graphene
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, relationship
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.exception import UnknownImageRegistry
from ai.backend.common.logging_utils import BraceStyleAdapter

from ..defs import PASSWORD_PLACEHOLDER
from .base import (
    Base,
    IDColumn,
    StrEnumType,
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

    association_container_registries_groups_rows = relationship(
        "AssociationContainerRegistriesGroupsRow",
        back_populates="container_registry_row",
        primaryjoin="ContainerRegistryRow.id == foreign(AssociationContainerRegistriesGroupsRow.registry_id)",
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

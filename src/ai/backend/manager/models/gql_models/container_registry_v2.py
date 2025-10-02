from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, TypeAlias

import graphene
import sqlalchemy as sa
from graphql import GraphQLError, Undefined

from ai.backend.logging import BraceStyleAdapter

from ..container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ..gql_relay import AsyncNode
from ..user import UserRole
from .container_registry import (
    AllowedGroups,
    ContainerRegistryNode,
    ContainerRegistryTypeField,
    handle_allowed_groups_update,
)

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


class CreateContainerRegistryNodeInputV2(graphene.InputObjectType):
    """
    Added in 25.3.0.
    """

    url = graphene.String(required=True, description="Added in 25.3.0.")
    type = ContainerRegistryTypeField(required=True, description="Added in 25.3.0.")
    registry_name = graphene.String(required=True, description="Added in 25.3.0.")
    is_global = graphene.Boolean(description="Added in 25.3.0.")
    project = graphene.String(description="Added in 25.3.0.")
    username = graphene.String(description="Added in 25.3.0.")
    password = graphene.String(description="Added in 25.3.0.")
    ssl_verify = graphene.Boolean(description="Added in 25.3.0.")
    extra = graphene.JSONString(description="Added in 25.3.0.")
    allowed_groups = AllowedGroups(description="Added in 25.3.0.")


class CreateContainerRegistryNodeV2(graphene.Mutation):
    class Meta:
        description = "Added in 25.3.0."

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        props = CreateContainerRegistryNodeInputV2(required=True, description="Added in 25.3.0.")

    container_registry = graphene.Field(ContainerRegistryNode)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        props: CreateContainerRegistryNodeInputV2,
    ) -> CreateContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context
        validator = ContainerRegistryValidator(
            ContainerRegistryValidatorArgs(
                url=props.url,
                type=props.type,
                project=props.project,
            )
        )

        validator.validate()

        input_config: dict[str, Any] = {
            "registry_name": props.registry_name,
            "url": props.url,
            "type": props.type,
        }

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("project", props.project)
        _set_if_set("username", props.username)
        _set_if_set("password", props.password)
        _set_if_set("ssl_verify", props.ssl_verify)
        _set_if_set("is_global", props.is_global)
        _set_if_set("extra", props.extra)

        try:
            async with ctx.db.begin_session() as db_session:
                reg_row = ContainerRegistryRow(**input_config)
                db_session.add(reg_row)
                await db_session.flush()
                await db_session.refresh(reg_row)

            if props.allowed_groups:
                await handle_allowed_groups_update(ctx.db, reg_row.id, props.allowed_groups)

            return cls(
                container_registry=ContainerRegistryNode.from_row(ctx, reg_row),
            )
        except Exception as e:
            raise GraphQLError(str(e))


class ModifyContainerRegistryNodeInputV2(graphene.InputObjectType):
    """
    Added in 25.3.0.
    """

    url = graphene.String(description="Added in 25.3.0.")
    type = ContainerRegistryTypeField(description="Added in 25.3.0.")
    registry_name = graphene.String(description="Added in 25.3.0.")
    is_global = graphene.Boolean(description="Added in 25.3.0.")
    project = graphene.String(description="Added in 25.3.0.")
    username = graphene.String(description="Added in 25.3.0.")
    password = graphene.String(description="Added in 25.3.0.")
    ssl_verify = graphene.Boolean(description="Added in 25.3.0.")
    extra = graphene.JSONString(description="Added in 25.3.0.")
    allowed_groups = AllowedGroups(description="Added in 25.3.0.")


class ModifyContainerRegistryNodeV2(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Meta:
        description = "Added in 25.3.0."

    container_registry = graphene.Field(ContainerRegistryNode)

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 25.3.0.",
        )
        props = ModifyContainerRegistryNodeInputV2(required=True, description="Added in 25.3.0.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        props: ModifyContainerRegistryNodeInputV2,
    ) -> ModifyContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {}

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("url", props.url)
        _set_if_set("type", props.type)
        _set_if_set("registry_name", props.registry_name)
        _set_if_set("username", props.username)
        _set_if_set("password", props.password)
        _set_if_set("project", props.project)
        _set_if_set("ssl_verify", props.ssl_verify)
        _set_if_set("is_global", props.is_global)
        _set_if_set("extra", props.extra)

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        try:
            async with ctx.db.begin_session() as session:
                stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
                reg_row = await session.scalar(stmt)

                if reg_row is None:
                    raise ValueError(f"ContainerRegistry not found (id: {reg_id})")
                for field, val in input_config.items():
                    setattr(reg_row, field, val)

                validator = ContainerRegistryValidator(
                    ContainerRegistryValidatorArgs(
                        type=reg_row.type,
                        project=reg_row.project,
                        url=reg_row.url,
                    )
                )

                validator.validate()

            if props.allowed_groups:
                await handle_allowed_groups_update(ctx.db, reg_row.id, props.allowed_groups)

            return cls(container_registry=ContainerRegistryNode.from_row(ctx, reg_row))

        except Exception as e:
            raise GraphQLError(str(e))


class DeleteContainerRegistryNodeV2(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Meta:
        description = "Added in 25.3.0."

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 25.3.0.",
        )

    container_registry = graphene.Field(ContainerRegistryNode)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
    ) -> DeleteContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        try:
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

        except Exception as e:
            raise GraphQLError(str(e))

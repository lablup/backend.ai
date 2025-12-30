from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, TypeAlias

import graphene
import sqlalchemy as sa
from graphql import GraphQLError, Undefined

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.logging import BraceStyleAdapter
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
                reg_row = ContainerRegistryRow(id=uuid.uuid4(), **input_config)
                db_session.add(reg_row)
                await db_session.flush()
                await db_session.refresh(reg_row)

                if props.allowed_groups:
                    await handle_allowed_groups_update(db_session, reg_row.id, props.allowed_groups)

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

    def to_action(self, registry_id: uuid.UUID) -> ModifyContainerRegistryAction:
        if self.allowed_groups is not Undefined:
            allowed_groups_model = AllowedGroupsModel(
                add=self.allowed_groups.add or [],
                remove=self.allowed_groups.remove or [],
            )
            allowed_groups_state = TriState.update(allowed_groups_model)
        else:
            allowed_groups_state = TriState.nop()

        return ModifyContainerRegistryAction(
            updater=Updater(
                spec=ContainerRegistryUpdaterSpec(
                    url=OptionalState.from_graphql(self.url),
                    type=OptionalState.from_graphql(self.type),
                    registry_name=OptionalState.from_graphql(self.registry_name),
                    is_global=TriState.from_graphql(self.is_global),
                    project=TriState.from_graphql(self.project),
                    username=TriState.from_graphql(self.username),
                    password=TriState.from_graphql(self.password),
                    ssl_verify=TriState.from_graphql(self.ssl_verify),
                    extra=TriState.from_graphql(self.extra),
                    allowed_groups=allowed_groups_state,
                ),
                pk_value=registry_id,
            )
        )


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

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        result = (
            await ctx.processors.container_registry.modify_container_registry.wait_for_complete(
                props.to_action(reg_id)
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


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

        result = (
            await ctx.processors.container_registry.delete_container_registry.wait_for_complete(
                DeleteContainerRegistryAction(
                    purger=Purger(row_class=ContainerRegistryRow, pk_value=reg_id)
                )
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))

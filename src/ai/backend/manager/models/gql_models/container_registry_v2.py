from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, TypeAlias

import graphene
import sqlalchemy as sa
from graphql import Undefined

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryModifier,
)
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from ..container_registry import (
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ..gql_relay import AsyncNode
from ..user import UserRole
from .container_registry import (
    AllowedGroups,
    ContainerRegistryNode,
    ContainerRegistryTypeField,
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
    project = graphene.String(required=True, description="Added in 25.3.0.")
    username = graphene.String(description="Added in 25.3.0.")
    password = graphene.String(description="Added in 25.3.0.")
    ssl_verify = graphene.Boolean(description="Added in 25.3.0.")
    extra = graphene.JSONString(description="Added in 25.3.0.")
    allowed_groups = AllowedGroups(description="Added in 25.3.0.")

    def to_action(self) -> CreateContainerRegistryAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        return CreateContainerRegistryAction(
            creator=ContainerRegistryCreator(
                url=self.url,
                type=self.type,
                registry_name=self.registry_name,
                is_global=value_or_none(self.is_global),
                project=self.project,
                username=value_or_none(self.username),
                password=value_or_none(self.password),
                ssl_verify=value_or_none(self.ssl_verify),
                extra=value_or_none(self.extra),
                allowed_groups=value_or_none(self.allowed_groups),
            )
        )


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
        action = props.to_action()
        result = (
            await ctx.processors.container_registry.create_container_registry.wait_for_complete(
                action
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(ctx, result.data))


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

    def to_modifier(self) -> ContainerRegistryModifier:
        return ContainerRegistryModifier(
            url=OptionalState.from_graphql(self.url),
            type=OptionalState.from_graphql(self.type),
            registry_name=OptionalState.from_graphql(self.registry_name),
            is_global=TriState.from_graphql(self.is_global),
            project=OptionalState.from_graphql(self.project),
            username=TriState.from_graphql(self.username),
            password=TriState.from_graphql(self.password),
            ssl_verify=TriState.from_graphql(self.ssl_verify),
            extra=TriState.from_graphql(self.extra),
            allowed_groups=TriState.from_graphql(self.allowed_groups),
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
                ModifyContainerRegistryAction(
                    id=reg_id,
                    modifier=props.to_modifier(),
                )
            )
        )

        return cls(container_registry=ContainerRegistryNode.from_dataclass(ctx, result.data))


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
                DeleteContainerRegistryAction(id=reg_id)
            )
        )

        return cls(container_registry=ContainerRegistryNode.from_dataclass(ctx, result.data))

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

import graphene
import sqlalchemy as sa
from graphql import Undefined

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.dto.manager.v2.container_registry.request import (
    CreateContainerRegistryInput as CreateContainerRegistryInputDTO,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryPurger
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryUpdater
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.update_container_registry import (
    UpdateContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .container_registry import (
    AllowedGroups,
    ContainerRegistryNode,
    ContainerRegistryTypeField,
)
from .gql_relay import AsyncNode

if TYPE_CHECKING:
    from .schema import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


type WhereClauseType = sa.sql.expression.BinaryExpression[Any] | sa.sql.expression.BooleanClauseList


class CreateContainerRegistryNodeInputV2(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_input(self) -> CreateContainerRegistryInputDTO:
        return CreateContainerRegistryInputDTO.model_validate(dict(self))


class CreateContainerRegistryNodeV2(graphene.Mutation):  # type: ignore[misc]
    class Meta:
        description = "Added in 25.3.0."

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        props = CreateContainerRegistryNodeInputV2(required=True, description="Added in 25.3.0.")

    container_registry = graphene.Field(ContainerRegistryNode)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        props: CreateContainerRegistryNodeInputV2,
    ) -> CreateContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context
        data = await ContainerRegistryAdapter(
            ctx.processors.container_registry, ctx.processors.rbac
        ).create_registry(props.to_input())
        return cls(container_registry=ContainerRegistryNode.from_dataclass(data))


class ModifyContainerRegistryNodeInputV2(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_allowed_groups(self) -> AllowedGroupsModel | None:
        """The projects to link and unlink, which the relation operations write beside
        the update."""
        if self.allowed_groups is Undefined:
            return None
        return AllowedGroupsModel(
            add=self.allowed_groups.add or [],
            remove=self.allowed_groups.remove or [],
        )

    def to_action(self, registry_id: uuid.UUID) -> UpdateContainerRegistryAction:
        return UpdateContainerRegistryAction(
            updater=ContainerRegistryUpdater(
                registry_id=ContainerRegistryID(registry_id),
                url=OptionalState.from_graphql(self.url),
                type=OptionalState.from_graphql(self.type),
                registry_name=OptionalState.from_graphql(self.registry_name),
                is_global=TriState.from_graphql(self.is_global),
                project=TriState.from_graphql(self.project),
                username=TriState.from_graphql(self.username),
                password=TriState.from_graphql(self.password),
                ssl_verify=TriState.from_graphql(self.ssl_verify),
                extra=TriState.from_graphql(self.extra),
            )
        )


class ModifyContainerRegistryNodeV2(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
        props: ModifyContainerRegistryNodeInputV2,
    ) -> ModifyContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        allowed_groups = props.to_allowed_groups()
        if allowed_groups is not None:
            await ContainerRegistryAdapter(
                ctx.processors.container_registry, ctx.processors.rbac
            ).apply_allowed_groups(ContainerRegistryID(reg_id), allowed_groups)
        result = await ctx.processors.container_registry.update_container_registry.run(
            props.to_action(reg_id)
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))


class DeleteContainerRegistryNodeV2(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
        info: graphene.ResolveInfo,
        id: str,
    ) -> DeleteContainerRegistryNodeV2:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        result = await ctx.processors.container_registry.delete_container_registry.run(
            DeleteContainerRegistryAction(
                purger=ContainerRegistryPurger(registry_id=ContainerRegistryID(reg_id))
            )
        )
        return cls(container_registry=ContainerRegistryNode.from_dataclass(result.data))

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

import graphene

from ai.backend.logging import BraceStyleAdapter

from ..base import BigInt
from ..rbac import ProjectScope, ScopeType
from ..user import UserRole
from .fields import ScopeField

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

if TYPE_CHECKING:
    from ai.backend.manager.models.gql import GraphQueryContext


class CreateContainerRegistryQuota(graphene.Mutation):
    """Added in 25.2.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = BigInt(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int | float,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope(_):
                    await graph_ctx.services_ctx.per_project_container_registries_quota.create(
                        scope_id, int(quota)
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))


class UpdateContainerRegistryQuota(graphene.Mutation):
    """Added in 25.2.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = BigInt(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int | float,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope(_):
                    await graph_ctx.services_ctx.per_project_container_registries_quota.update(
                        scope_id, int(quota)
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))


class DeleteContainerRegistryQuota(graphene.Mutation):
    """Added in 25.2.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        try:
            match scope_id:
                case ProjectScope(_):
                    await graph_ctx.services_ctx.per_project_container_registries_quota.delete(
                        scope_id
                    )
                case _:
                    raise NotImplementedError("Only project scope is supported for now.")

            return cls(ok=True, msg="success")
        except Exception as e:
            return cls(ok=False, msg=str(e))

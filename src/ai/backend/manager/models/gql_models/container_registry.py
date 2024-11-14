from __future__ import annotations

import enum
import logging
from typing import Self

import graphene

from ai.backend.logging import BraceStyleAdapter

from ..base import BigInt
from ..rbac import ScopeType
from ..user import UserRole
from .container_registry_utils import HarborQuotaManager
from .fields import ScopeField

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


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
        async with info.context.db.begin_session() as db_sess:
            try:
                manager = await HarborQuotaManager.new(db_sess, scope_id)
                await manager.create(int(quota))
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
        async with info.context.db.begin_session() as db_sess:
            try:
                manager = await HarborQuotaManager.new(db_sess, scope_id)
                await manager.update(int(quota))
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
        async with info.context.db.begin_session() as db_sess:
            try:
                manager = await HarborQuotaManager.new(db_sess, scope_id)
                await manager.delete()
                return cls(ok=True, msg="success")
            except Exception as e:
                return cls(ok=False, msg=str(e))

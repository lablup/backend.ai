from __future__ import annotations

import logging
from typing import Self

import graphene
import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter

from ..association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ..base import BigInt, simple_db_mutate
from ..rbac import ScopeType
from ..user import UserRole
from .container_registry_utils import HarborQuotaManager
from .fields import ScopeField

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class AssociateContainerRegistryWithGroup(graphene.Mutation):
    """Added in 25.1.0."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        registry_id = graphene.String(required=True)
        group_id = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        registry_id: str,
        group_id: str,
    ) -> Self:
        insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values({
            "registry_id": registry_id,
            "group_id": group_id,
        })
        return await simple_db_mutate(cls, info.context, insert_query)


class DisassociateContainerRegistryWithGroup(graphene.Mutation):
    """Added in 25.1.0."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        registry_id = graphene.String(required=True)
        group_id = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        registry_id: str,
        group_id: str,
    ) -> Self:
        delete_query = (
            sa.delete(AssociationContainerRegistriesGroupsRow)
            .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
            .where(AssociationContainerRegistriesGroupsRow.group_id == group_id)
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class CreateContainerRegistryQuota(graphene.Mutation):
    """Added in 25.01.0."""

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
    """Added in 25.01.0."""

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
    """Added in 25.01.0."""

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

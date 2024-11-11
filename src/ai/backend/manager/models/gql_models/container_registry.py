from __future__ import annotations

import logging
from typing import Self

import graphene
import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import simple_db_mutate

from .user import UserRole

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class AssociateContainerRegistryWithGroup(graphene.Mutation):
    """Added in 24.12.0."""

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
    """Added in 24.12.0."""

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

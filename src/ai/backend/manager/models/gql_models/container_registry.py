from __future__ import annotations

import logging
from typing import Any, Self

import aiohttp
import aiohttp.client_exceptions
import graphene
import sqlalchemy as sa
import yarl
from sqlalchemy.orm import load_only

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow, ContainerRegistryType
from ai.backend.manager.models.gql_models.fields import ScopeField
from ai.backend.manager.models.group import GroupRow

from ..association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ..base import simple_db_mutate
from ..rbac import ProjectScope, ScopeType
from ..user import UserRole

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


class UpdateQuota(graphene.Mutation):
    """Added in 24.12.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = graphene.Int(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int,
    ) -> Self:
        graph_ctx = info.context

        # TODO: Support other scope types
        assert isinstance(scope_id, ProjectScope)
        project_id = scope_id.project_id

        # user = graph_ctx.user
        # client_ctx = ClientContext(
        #     graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
        # )

        async with graph_ctx.db.begin_session() as db_sess:
            group_query = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(load_only(GroupRow.container_registry))
            )
            result = await db_sess.execute(group_query)

            group = result.scalar_one_or_none()

            if (
                group is None
                or group.container_registry is None
                or "registry" not in group.container_registry
                or "project" not in group.container_registry
            ):
                raise ValueError("Container registry info does not exist in the group.")

            registry_name, project = (
                group.container_registry["registry"],
                group.container_registry["project"],
            )

            cr_query = sa.select(ContainerRegistryRow).where(
                (ContainerRegistryRow.registry_name == registry_name)
                & (ContainerRegistryRow.project == project)
            )

            result = await db_sess.execute(cr_query)
            registry = result.fetchone()[0]

            if registry.type != ContainerRegistryType.HARBOR2:
                raise ValueError("Only HarborV2 registry is supported for now.")

        ssl_verify = registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)

        url = yarl.URL(registry.url)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                registry.username,
                registry.password,
            )

            get_project_id = url / "api" / "v2.0" / "projects" / project

            async with sess.get(get_project_id, allow_redirects=False, **rqst_args) as resp:
                res = await resp.json()
                harbor_project_id = res["project_id"]

            get_quota_id = (url / "api" / "v2.0" / "quotas").with_query({
                "reference": "project",
                "reference_id": harbor_project_id,
            })

            async with sess.get(get_quota_id, allow_redirects=False, **rqst_args) as resp:
                res = await resp.json()
                # TODO: Raise error when quota is not found or multiple quotas are found.
                quota_id = res[0]["id"]

            put_quota_url = url / "api" / "v2.0" / "quotas" / str(quota_id)
            update_payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_url, json=update_payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status == 200:
                    return UpdateQuota(ok=True, msg="Quota updated successfully.")
                else:
                    log.error(f"Failed to update quota: {await resp.json()}")
                    return UpdateQuota(
                        ok=False, msg=f"Failed to update quota. Status code: {resp.status}"
                    )

        return UpdateQuota(ok=False, msg="Unknown error!")

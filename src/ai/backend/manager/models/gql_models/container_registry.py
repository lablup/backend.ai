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

from ..association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ..base import simple_db_mutate
from ..container_registry import ContainerRegistryRow, ContainerRegistryType
from ..rbac import ProjectScope, ScopeType
from ..user import UserRole
from .fields import ScopeField
from .group import GroupRow

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


async def update_harbor_project_quota(
    cls: Any, info: graphene.ResolveInfo, scope_id: ScopeType, quota: int
) -> Any:
    if not isinstance(scope_id, ProjectScope):
        return cls(ok=False, msg="Quota mutation currently supports only the project scope.")

    project_id = scope_id.project_id
    graph_ctx = info.context

    async with graph_ctx.db.begin_session() as db_sess:
        group_query = (
            sa.select(GroupRow)
            .where(GroupRow.id == project_id)
            .options(load_only(GroupRow.container_registry))
        )
        result = await db_sess.execute(group_query)
        group_row = result.scalar_one_or_none()

        if (
            not group_row
            or not group_row.container_registry
            or "registry" not in group_row.container_registry
            or "project" not in group_row.container_registry
        ):
            return UpdateQuota(
                ok=False,
                msg=f"Container registry info does not exist in the group. (gr: {project_id})",
            )

        registry_name, project = (
            group_row.container_registry["registry"],
            group_row.container_registry["project"],
        )

        registry_query = sa.select(ContainerRegistryRow).where(
            (ContainerRegistryRow.registry_name == registry_name)
            & (ContainerRegistryRow.project == project)
        )

        result = await db_sess.execute(registry_query)
        registry = result.scalars().one_or_none()

        if not registry:
            return cls(
                ok=False,
                msg=f"Specified container registry row does not exist. (cr: {registry_name}, gr: {project})",
            )

        if registry.type != ContainerRegistryType.HARBOR2:
            return cls(ok=False, msg="Only HarborV2 registry is supported for now.")

    ssl_verify = registry.ssl_verify
    connector = aiohttp.TCPConnector(ssl=ssl_verify)

    api_url = yarl.URL(registry.url) / "api" / "v2.0"
    async with aiohttp.ClientSession(connector=connector) as sess:
        rqst_args: dict[str, Any] = {}
        rqst_args["auth"] = aiohttp.BasicAuth(
            registry.username,
            registry.password,
        )

        get_project_id_api = api_url / "projects" / project

        async with sess.get(get_project_id_api, allow_redirects=False, **rqst_args) as resp:
            res = await resp.json()
            harbor_project_id = res["project_id"]

            get_quota_id_api = (api_url / "quotas").with_query({
                "reference": "project",
                "reference_id": harbor_project_id,
            })

        async with sess.get(get_quota_id_api, allow_redirects=False, **rqst_args) as resp:
            res = await resp.json()
            if not res:
                return cls(
                    ok=False, msg=f"Quota entity not found. (project_id: {harbor_project_id})"
                )
            if len(res) > 1:
                return cls(
                    ok=False,
                    msg=f"Multiple quota entity found. (project_id: {harbor_project_id})",
                )

            quota_id = res[0]["id"]

            put_quota_api = api_url / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

        async with sess.put(
            put_quota_api, json=payload, allow_redirects=False, **rqst_args
        ) as resp:
            if resp.status == 200:
                return cls(ok=True, msg="Quota updated successfully.")
            else:
                log.error(f"Failed to update quota: {await resp.json()}")
                return cls(ok=False, msg=f"Failed to update quota. Status code: {resp.status}")

    return cls(ok=False, msg="Unknown error!")


class CreateQuota(graphene.Mutation):
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
        return await update_harbor_project_quota(cls, info, scope_id, quota)


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
        return await update_harbor_project_quota(cls, info, scope_id, quota)


class DeleteQuota(graphene.Mutation):
    """Added in 24.12.0."""

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
        return await update_harbor_project_quota(cls, info, scope_id, -1)

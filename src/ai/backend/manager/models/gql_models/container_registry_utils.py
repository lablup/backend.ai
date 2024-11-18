from __future__ import annotations

import logging
from typing import Any, Literal, Optional

import aiohttp
import aiohttp.client_exceptions
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    ContainerRegistryNotFound,
    GenericBadRequest,
    InternalServerError,
    NotImplementedAPI,
    ObjectNotFound,
)

from ...container_registry import ContainerRegistryRow
from ..association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ..group import GroupRow
from ..rbac import ProjectScope, ScopeType

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


async def handle_harbor_project_quota_operation(
    operation_type: Literal["create", "read", "update", "delete"],
    db_sess: SASession,
    scope_id: ScopeType,
    quota: Optional[int],
) -> Optional[int]:
    """
    Utility function for code reuse of the HarborV2 per-project Quota CRUD API.

    :param quota: Required for create and delete operations. For all other operations, this parameter should be set to None.
    :return: The current quota value for read operations. For other operations, returns None.
    """
    if not isinstance(scope_id, ProjectScope):
        raise NotImplementedAPI("Quota mutation currently supports only the project scope.")

    if operation_type in ("create", "update"):
        assert quota is not None, "Quota value is required for create/update operation."
    else:
        assert quota is None, "Quota value must be None for read/delete operation."

    project_id = scope_id.project_id
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
        raise ContainerRegistryNotFound(
            f"Container registry info does not exist or is invalid in the group. (gr: {project_id})"
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
        raise ContainerRegistryNotFound(
            f"Specified container registry row does not exist. (cr: {registry_name}, gr: {project})"
        )

    if operation_type == "read" and not registry.is_global:
        get_assoc_query = sa.select(
            sa.exists()
            .where(AssociationContainerRegistriesGroupsRow.registry_id == registry.id)
            .where(AssociationContainerRegistriesGroupsRow.group_id == group_row.row_id)
        )
        assoc_exist = (await db_sess.execute(get_assoc_query)).scalar()

        if not assoc_exist:
            raise ValueError("The group is not associated with the container registry.")

    ssl_verify = registry.ssl_verify
    connector = aiohttp.TCPConnector(ssl=ssl_verify)
    async with aiohttp.ClientSession(connector=connector) as sess:
        rqst_args: dict[str, Any] = {}
        rqst_args["auth"] = aiohttp.BasicAuth(
            registry.username,
            registry.password,
        )

        api_url = yarl.URL(registry.url) / "api" / "v2.0"
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
                raise ObjectNotFound(object_name="quota entity")
            if len(res) > 1:
                raise InternalServerError(
                    f"Multiple quota entities found. (project_id: {harbor_project_id})"
                )

            previous_quota = res[0]["hard"]["storage"]

            if operation_type == "create":
                if previous_quota > 0:
                    raise GenericBadRequest(f"Quota limit already exists. (gr: {project_id})")
            else:
                if previous_quota == -1:
                    raise ObjectNotFound(object_name="quota entity")

            if operation_type == "read":
                return previous_quota

            quota_id = res[0]["id"]

            put_quota_api = api_url / "quotas" / str(quota_id)
            quota = quota if operation_type != "delete" else -1
            payload = {"hard": {"storage": quota}}

        async with sess.put(
            put_quota_api, json=payload, allow_redirects=False, **rqst_args
        ) as resp:
            if resp.status == 200:
                return None
            else:
                log.error(f"Failed to {operation_type} quota: {await resp.json()}")
                raise InternalServerError(
                    f"Failed to {operation_type} quota. Status code: {resp.status}"
                )

    raise InternalServerError("Unknown error!")

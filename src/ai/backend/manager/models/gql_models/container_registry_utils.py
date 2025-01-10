from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, TypedDict

import aiohttp
import aiohttp.client_exceptions
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only

from ai.backend.common.types import aobject
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    ContainerRegistryNotFound,
    GenericBadRequest,
    InternalServerError,
    NotImplementedAPI,
    ObjectNotFound,
)

from ..association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ..group import GroupRow
from ..rbac import ProjectScope, ScopeType

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

if TYPE_CHECKING:
    from ..container_registry import ContainerRegistryRow


class HarborQuotaInfo(TypedDict):
    previous_quota: int
    quota_id: int


class HarborQuotaManager(aobject):
    """
    Utility class for HarborV2 per-project Quota CRUD API.
    """

    db_sess: SASession
    scope_id: ScopeType
    group_row: GroupRow
    registry: ContainerRegistryRow
    project: str
    project_id: uuid.UUID

    def __init__(self, db_sess: SASession, scope_id: ScopeType):
        if not isinstance(scope_id, ProjectScope):
            raise NotImplementedAPI("Quota mutation currently supports only the project scope.")

        self.db_sess = db_sess
        self.scope_id = scope_id

    async def __ainit__(self) -> None:
        from ..container_registry import ContainerRegistryRow

        assert isinstance(self.scope_id, ProjectScope)

        project_id = self.scope_id.project_id
        group_query = (
            sa.select(GroupRow)
            .where(GroupRow.id == project_id)
            .options(load_only(GroupRow.container_registry))
        )
        result = await self.db_sess.execute(group_query)
        group_row = result.scalar_one_or_none()

        if not HarborQuotaManager._is_valid_group_row(group_row):
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

        result = await self.db_sess.execute(registry_query)
        registry = result.scalars().one_or_none()

        if not registry:
            raise ContainerRegistryNotFound(
                f"Specified container registry row not found. (cr: {registry_name}, gr: {project})"
            )

        self.group_row = group_row
        self.registry = registry
        self.project = project
        self.project_id = project_id

    @classmethod
    def _is_valid_group_row(cls, group_row: GroupRow) -> bool:
        return (
            group_row
            and group_row.container_registry
            and "registry" in group_row.container_registry
            and "project" in group_row.container_registry
        )

    async def _get_harbor_project_id(
        self, sess: aiohttp.ClientSession, rqst_args: dict[str, Any]
    ) -> str:
        get_project_id_api = (
            yarl.URL(self.registry.url) / "api" / "v2.0" / "projects" / self.project
        )

        async with sess.get(get_project_id_api, allow_redirects=False, **rqst_args) as resp:
            if resp.status != 200:
                raise InternalServerError(f"Failed to get harbor project_id! response: {resp}")

            res = await resp.json()
            harbor_project_id = res["project_id"]
            return harbor_project_id

    async def _get_quota_info(
        self, sess: aiohttp.ClientSession, rqst_args: dict[str, Any]
    ) -> HarborQuotaInfo:
        harbor_project_id = await self._get_harbor_project_id(sess, rqst_args)
        get_quota_id_api = (yarl.URL(self.registry.url) / "api" / "v2.0" / "quotas").with_query({
            "reference": "project",
            "reference_id": harbor_project_id,
        })

        async with sess.get(get_quota_id_api, allow_redirects=False, **rqst_args) as resp:
            if resp.status != 200:
                raise InternalServerError(f"Failed to get quota info! response: {resp}")

            res = await resp.json()
            if not res:
                raise ObjectNotFound(object_name="quota entity")
            if len(res) > 1:
                raise InternalServerError(
                    f"Multiple quota entities found. (project_id: {harbor_project_id})"
                )

            previous_quota = res[0]["hard"]["storage"]
            quota_id = res[0]["id"]

            return HarborQuotaInfo(previous_quota=previous_quota, quota_id=quota_id)

    async def read(self) -> int:
        if not self.registry.is_global:
            get_assoc_query = sa.select(
                sa.exists()
                .where(AssociationContainerRegistriesGroupsRow.registry_id == self.registry.id)
                .where(AssociationContainerRegistriesGroupsRow.group_id == self.group_row.row_id)
            )
            assoc_exist = (await self.db_sess.execute(get_assoc_query)).scalar()

            if not assoc_exist:
                raise ValueError("The group is not associated with the container registry.")

        ssl_verify = self.registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.registry.username,
                self.registry.password,
            )

            previous_quota = (await self._get_quota_info(sess, rqst_args))["previous_quota"]
            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            return previous_quota

    async def create(self, quota: int) -> None:
        ssl_verify = self.registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.registry.username,
                self.registry.password,
            )

            quota_info = await self._get_quota_info(sess, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota > 0:
                raise GenericBadRequest(f"Quota limit already exists. (gr: {self.project_id})")

            put_quota_api = yarl.URL(self.registry.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to create quota! response: {resp}")
                    raise InternalServerError(f"Failed to create quota! response: {resp}")

    async def update(self, quota: int) -> None:
        ssl_verify = self.registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.registry.username,
                self.registry.password,
            )

            quota_info = await self._get_quota_info(sess, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(self.registry.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to update quota! response: {resp}")
                    raise InternalServerError(f"Failed to update quota! response: {resp}")

    async def delete(self) -> None:
        ssl_verify = self.registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                self.registry.username,
                self.registry.password,
            )

            quota_info = await self._get_quota_info(sess, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(self.registry.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": -1}}  # setting quota to -1 means delete

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to delete quota! response: {resp}")
                    raise InternalServerError(f"Failed to delete quota! response: {resp}")

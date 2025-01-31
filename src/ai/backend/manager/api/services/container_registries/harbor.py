from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

import aiohttp
import yarl

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import GenericBadRequest, InternalServerError, ObjectNotFound
from ai.backend.manager.api.services.container_registries.base import (
    ContainerRegistryRow,
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.models.rbac import ProjectScope

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__ = (
    "AbstractPerProjectRegistryQuotaClient",
    "PerProjectHarborQuotaClient",
    "PerProjectRegistryQuotaRepository",
    "PerProjectContainerRegistryQuotaProtocol",
    "PerProjectContainerRegistryQuotaService",
)


class HarborProjectQuotaInfo(TypedDict):
    previous_quota: int
    quota_id: int


class AbstractPerProjectRegistryQuotaClient(Protocol):
    async def create(self, registry_row: ContainerRegistryRow, quota: int) -> None: ...
    async def update(self, registry_row: ContainerRegistryRow, quota: int) -> None: ...
    async def delete(self, registry_row: ContainerRegistryRow) -> None: ...
    async def read(self, registry_row: ContainerRegistryRow) -> int: ...


class PerProjectHarborQuotaClient(AbstractPerProjectRegistryQuotaClient):
    async def _get_harbor_project_id(
        self,
        sess: aiohttp.ClientSession,
        registry_row: ContainerRegistryRow,
        rqst_args: dict[str, Any],
    ) -> str:
        get_project_id_api = (
            yarl.URL(registry_row.url) / "api" / "v2.0" / "projects" / registry_row.project
        )

        async with sess.get(get_project_id_api, allow_redirects=False, **rqst_args) as resp:
            if resp.status != 200:
                raise InternalServerError(f"Failed to get harbor project_id! response: {resp}")

            res = await resp.json()
            harbor_project_id = res["project_id"]
            return str(harbor_project_id)

    async def _get_quota_info(
        self,
        sess: aiohttp.ClientSession,
        registry_row: ContainerRegistryRow,
        rqst_args: dict[str, Any],
    ) -> HarborProjectQuotaInfo:
        harbor_project_id = await self._get_harbor_project_id(sess, registry_row, rqst_args)
        get_quota_id_api = (yarl.URL(registry_row.url) / "api" / "v2.0" / "quotas").with_query({
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
            return HarborProjectQuotaInfo(previous_quota=previous_quota, quota_id=quota_id)

    async def read(self, registry_row: ContainerRegistryRow) -> int:
        ssl_verify = True
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}

            quota_info = await self._get_quota_info(sess, registry_row, rqst_args)
            previous_quota = quota_info["previous_quota"]
            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")
            return previous_quota

    async def create(self, registry_row: ContainerRegistryRow, quota: int) -> None:
        ssl_verify = True
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(registry_row.username, registry_row.password)

            quota_info = await self._get_quota_info(sess, registry_row, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota > 0:
                raise GenericBadRequest("Quota limit already exists!")

            put_quota_api = yarl.URL(registry_row.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to create quota! response: {resp}")
                    raise InternalServerError(f"Failed to create quota! response: {resp}")

    async def update(self, registry_row: ContainerRegistryRow, quota: int) -> None:
        ssl_verify = True
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(registry_row.username, registry_row.password)

            quota_info = await self._get_quota_info(sess, registry_row, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(registry_row.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to update quota! response: {resp}")
                    raise InternalServerError(f"Failed to update quota! response: {resp}")

    async def delete(self, registry_row: ContainerRegistryRow) -> None:
        ssl_verify = True
        connector = aiohttp.TCPConnector(ssl=ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(registry_row.username, registry_row.password)

            quota_info = await self._get_quota_info(sess, registry_row, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(registry_row.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": -1}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to delete quota! response: {resp}")
                    raise InternalServerError(f"Failed to delete quota! response: {resp}")


class PerProjectContainerRegistryQuotaProtocol(Protocol):
    async def create(self, scope_id: ProjectScope, quota: int) -> None: ...
    async def update(self, scope_id: ProjectScope, quota: int) -> None: ...
    async def delete(self, scope_id: ProjectScope) -> None: ...
    async def read(self, scope_id: ProjectScope) -> int: ...


class PerProjectContainerRegistryQuotaService(PerProjectContainerRegistryQuotaProtocol):
    repository: PerProjectRegistryQuotaRepository

    def __init__(self, repository: PerProjectRegistryQuotaRepository):
        self.repository = repository

    def make_client(self, type_: ContainerRegistryType) -> AbstractPerProjectRegistryQuotaClient:
        match type_:
            case ContainerRegistryType.HARBOR2:
                return PerProjectHarborQuotaClient()
            case _:
                raise GenericBadRequest(
                    f"{type_} does not support registry quota per project management."
                )

    async def create(self, scope_id: ProjectScope, quota: int) -> None:
        registry_row = await self.repository.fetch_container_registry_row(scope_id)
        await self.make_client(registry_row.type).create(registry_row, quota)

    async def update(self, scope_id: ProjectScope, quota: int) -> None:
        registry_row = await self.repository.fetch_container_registry_row(scope_id)
        await self.make_client(registry_row.type).update(registry_row, quota)

    async def delete(self, scope_id: ProjectScope) -> None:
        registry_row = await self.repository.fetch_container_registry_row(scope_id)
        await self.make_client(registry_row.type).delete(registry_row)

    async def read(self, scope_id: ProjectScope) -> int:
        registry_row = await self.repository.fetch_container_registry_row(scope_id)
        return await self.make_client(registry_row.type).read(registry_row)

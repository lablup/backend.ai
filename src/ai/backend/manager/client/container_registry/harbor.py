from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING, Any, override

import aiohttp
import yarl

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    InternalServerError,
    ObjectNotFound,
)

if TYPE_CHECKING:
    from ai.backend.manager.service.container_registry.harbor import (
        HarborAuthArgs,
        HarborProjectInfo,
        HarborProjectQuotaInfo,
    )

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_harbor_auth_args(auth_args: HarborAuthArgs) -> dict[str, Any]:
    return {"auth": aiohttp.BasicAuth(auth_args["username"], auth_args["password"])}


class AbstractPerProjectRegistryQuotaClient(abc.ABC):
    async def create_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        raise NotImplementedError

    async def update_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        raise NotImplementedError

    async def delete_quota(
        self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs
    ) -> None:
        raise NotImplementedError

    async def read_quota(self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs) -> int:
        raise NotImplementedError


class PerProjectHarborQuotaClient(AbstractPerProjectRegistryQuotaClient):
    async def _get_harbor_project_id(
        self,
        sess: aiohttp.ClientSession,
        project_info: HarborProjectInfo,
        rqst_args: dict[str, Any],
    ) -> str:
        get_project_id_api = (
            yarl.URL(project_info.url) / "api" / "v2.0" / "projects" / project_info.project
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
        project_info: HarborProjectInfo,
        rqst_args: dict[str, Any],
    ) -> HarborProjectQuotaInfo:
        from ...service.container_registry.harbor import HarborProjectQuotaInfo

        harbor_project_id = await self._get_harbor_project_id(sess, project_info, rqst_args)
        get_quota_id_api = (yarl.URL(project_info.url) / "api" / "v2.0" / "quotas").with_query({
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

    @override
    async def read_quota(self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs) -> int:
        connector = aiohttp.TCPConnector(ssl=project_info.ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args = _get_harbor_auth_args(auth_args)
            quota_info = await self._get_quota_info(sess, project_info, rqst_args)
            previous_quota = quota_info["previous_quota"]
            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")
            return previous_quota

    @override
    async def create_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        connector = aiohttp.TCPConnector(ssl=project_info.ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args = _get_harbor_auth_args(auth_args)
            quota_info = await self._get_quota_info(sess, project_info, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota > 0:
                raise GenericBadRequest("Quota limit already exists!")

            put_quota_api = yarl.URL(project_info.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to create quota! response: {resp}")
                    raise InternalServerError(f"Failed to create quota! response: {resp}")

    @override
    async def update_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        connector = aiohttp.TCPConnector(ssl=project_info.ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args = _get_harbor_auth_args(auth_args)
            quota_info = await self._get_quota_info(sess, project_info, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(project_info.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to update quota! response: {resp}")
                    raise InternalServerError(f"Failed to update quota! response: {resp}")

    @override
    async def delete_quota(
        self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs
    ) -> None:
        connector = aiohttp.TCPConnector(ssl=project_info.ssl_verify)
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args = _get_harbor_auth_args(auth_args)
            quota_info = await self._get_quota_info(sess, project_info, rqst_args)
            previous_quota, quota_id = quota_info["previous_quota"], quota_info["quota_id"]

            if previous_quota == -1:
                raise ObjectNotFound(object_name="quota entity")

            put_quota_api = yarl.URL(project_info.url) / "api" / "v2.0" / "quotas" / str(quota_id)
            payload = {"hard": {"storage": -1}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status != 200:
                    log.error(f"Failed to delete quota! response: {resp}")
                    raise InternalServerError(f"Failed to delete quota! response: {resp}")

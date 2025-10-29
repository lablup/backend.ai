from __future__ import annotations

import asyncio
import logging
import uuid
from functools import partial
from typing import Any, Optional

import aiohttp
from pydantic_core._pydantic_core import ValidationError

from ai.backend.common.clients.http_client import ClientKey, ClientPool, tcp_client_session_factory
from ai.backend.common.exception import (
    BaseNFSMountCheckFailed,
    ExportPathNotFound,
    ShowmountNotFound,
)
from ai.backend.common.utils import check_nfs_remote_server
from ai.backend.logging import BraceStyleAdapter

from .exception import (
    AuthenticationError,
    ShareNotFound,
)
from .request import ClusterMetricParams, CreateShareParams, GetShareParams
from .schema.metric import Metric
from .schema.objective import Objective
from .schema.share import Share, SimpleShare
from .schema.site import Site
from .types import APIConnectionInfo

DOMAIN_FOR_HTTP_SESSION = "hammerspace"
NFS_CHECK_RETRY_COUNT = 5
NFS_CHECK_WAIT_SEC = 1

log = BraceStyleAdapter(logging.getLogger(__name__))


class HammerspaceAPIClient:
    def __init__(
        self,
        connection_info: APIConnectionInfo,
    ) -> None:
        custom_session_factory = partial(
            tcp_client_session_factory,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            ssl=connection_info.ssl_enabled,
        )
        self._client_pool = ClientPool(custom_session_factory)
        self._connection_info = connection_info

    def _create_session(self, key: ClientKey) -> aiohttp.ClientSession:
        session = self._client_pool.load_client_session(key)
        return session

    async def _login(self) -> aiohttp.ClientSession:
        session = self._create_session(
            ClientKey(str(self._connection_info.address), DOMAIN_FOR_HTTP_SESSION)
        )
        async with session.post(
            self._connection_info.address / "login",
            data={
                "username": self._connection_info.username,
                "password": self._connection_info.password,
            },
            ssl=self._connection_info.ssl_enabled,
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if resp.status // 100 == 4:
                    err_msg = repr(e)
                    raise AuthenticationError(
                        "Hammerspace authentication failed. "
                        f"username: {self._connection_info.username}, err: {err_msg}"
                    ) from e
                raise
        return session

    async def try_login(self) -> None:
        await self._login()

    async def _create_login_session(self) -> aiohttp.ClientSession:
        session = await self._login()
        return session

    async def _check_nfs_export(self, export_path: str) -> None:
        host = self._connection_info.address.host
        if host is None:
            log.warning(
                "Invalid host in the address: {}, skip NFS export check",
                self._connection_info.address,
            )
            return
        count = NFS_CHECK_RETRY_COUNT
        while count > 0:
            count -= 1
            try:
                await check_nfs_remote_server(host, export_path)
            except ShowmountNotFound:
                log.warning("showmount command not found. Install nfs-common package.")
                return
            except ExportPathNotFound:
                log.debug(
                    "NFS export path {} not found on the server {}. Retrying...", export_path, host
                )
            except BaseNFSMountCheckFailed:
                log.exception(
                    "Check NFS export {} on the server {} failed. Retrying...", export_path, host
                )
            else:
                log.debug("Found NFS export {} on the server {}", export_path, host)
                return
            await asyncio.sleep(NFS_CHECK_WAIT_SEC)
        log.exception("Failed to verify NFS export {} on the server {}", export_path, host)

    async def create_share(
        self,
        params: CreateShareParams,
        retry: int,
        wait_sec: int,
    ) -> SimpleShare:
        session = await self._create_login_session()
        async with session.post(
            self._connection_info.address / "shares",
            params=params.query(),
            json=params.body(),
            ssl=self._connection_info.ssl_enabled,
        ) as resp:
            resp.raise_for_status()

        while retry > 0:
            log.debug(
                "Retrying to get the created share: {}, remaining retries: {}", params.name, retry
            )
            raw_shares = await self._get_shares(session, GetShareParams(name=params.name))
            for raw_share in raw_shares:
                try:
                    share = SimpleShare.model_validate(raw_share)
                    if share.name == params.name:
                        await self._check_nfs_export(share.path)
                        return share
                except ValidationError:
                    continue
            retry -= 1
            await asyncio.sleep(wait_sec)  # wait for a moment and try again
        raise ShareNotFound(f"Failed to get the created share: {params.name}")

    async def _get_shares(
        self, session: aiohttp.ClientSession, params: GetShareParams
    ) -> list[dict[str, Any]]:
        session = await self._create_login_session()
        async with session.get(
            self._connection_info.address / "shares",
            params=params.query(),
            ssl=self._connection_info.ssl_enabled,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data

    async def get_share(
        self,
        params: GetShareParams,
    ) -> Optional[Share]:
        session = await self._create_login_session()
        data = await self._get_shares(session, params)
        for raw_share in data:
            try:
                share = Share.model_validate(raw_share)
                if share.name == params.name:
                    return share
            except ValidationError:
                continue
        return None

    async def poll_share(
        self,
        params: GetShareParams,
        retry: int,
        wait_sec: int,
    ) -> Optional[Share]:
        session = await self._create_login_session()
        while retry > 0:
            data = await self._get_shares(session, params)
            for raw_share in data:
                try:
                    share = Share.model_validate(raw_share)
                except ValidationError:
                    continue
                if share.name == params.name:
                    return share
            retry -= 1
            await asyncio.sleep(wait_sec)  # wait for a moment and try again
        return None

    async def get_objective(self, id: uuid.UUID) -> Optional[Objective]:
        session = await self._create_login_session()
        query = {"spec": f"uoid.uuid=eq={id}"}
        async with session.get(self._connection_info.address / "objectives", params=query) as resp:
            resp.raise_for_status()
            data = await resp.json()
            objectives = [Objective.model_validate(obj) for obj in data]
            for obj in objectives:
                if obj.uoid.uuid == id:
                    return obj
            return None

    async def get_sites(self) -> list[Site]:
        session = await self._create_login_session()
        async with session.get(self._connection_info.address / "sites") as resp:
            resp.raise_for_status()
            data = await resp.json()
            sites: list[Site] = []
            for s in data:
                try:
                    site = Site.model_validate(s)
                    sites.append(site)
                except ValidationError:
                    log.warning("Failed to parse the site data: {}", s)
                    continue
            return sites

    async def get_cluster_metrics(self, params: ClusterMetricParams) -> Metric:
        session = await self._create_login_session()
        async with session.get(
            self._connection_info.address
            / f"metrics/capacity/{params.object_type}/{params.site_id}",
            params=params.query(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            metric = Metric.model_validate(data)
            return metric

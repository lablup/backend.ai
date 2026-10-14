from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Final, cast

import aiohttp
from yarl import URL

from ai.backend.common.clients.storage_backends.hammerspace.dto import (
    HammerspaceClusterMetricQuery,
    HammerspaceCreateShareQuery,
    HammerspaceCreateShareRequest,
    HammerspaceGetObjectiveQuery,
    HammerspaceGetShareQuery,
    HammerspaceLoginRequest,
    Metric,
    Objective,
    Share,
    SimpleShare,
    Site,
)
from ai.backend.common.clients.storage_backends.hammerspace.exceptions import (
    AuthenticationError,
    ShareNotFound,
)
from ai.backend.common.clients.storage_backends.hammerspace.types import ObjectType
from ai.backend.common.exception import (
    BackendAISchemaValidationFailed,
    BaseNFSMountCheckFailed,
    ExportPathNotFound,
    ShowmountNotFound,
)
from ai.backend.common.utils import check_nfs_remote_server
from ai.backend.logging.structured import StructuredLogger

NFS_CHECK_RETRY_COUNT: Final = 5
NFS_CHECK_WAIT_SEC: Final = 1

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class HammerspaceAPIClientArgs:
    address: str
    username: str
    password: str
    ssl_enabled: bool


class HammerspaceAPIClient:
    """Hammerspace REST API client using a cookie session.

    The caller logs in with ``login()`` whenever ``is_logged_in`` is false.
    """

    _address: URL
    _username: str
    _password: str
    _ssl_enabled: bool
    _logged_in: bool
    _session: aiohttp.ClientSession

    def __init__(self, args: HammerspaceAPIClientArgs) -> None:
        self._address = URL(args.address)
        self._username = args.username
        self._password = args.password
        self._ssl_enabled = args.ssl_enabled
        self._logged_in = False
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=args.ssl_enabled),
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        )

    async def aclose(self) -> None:
        await self._session.close()

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    async def login(self) -> None:
        self._logged_in = False
        async with self._session.post(
            self._address / "login",
            data=HammerspaceLoginRequest(
                username=self._username, password=self._password
            ).model_dump(mode="json", by_alias=True),
            ssl=self._ssl_enabled,
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if resp.status // 100 == 4:
                    raise AuthenticationError(
                        f"Hammerspace authentication failed. username: {self._username}, err: {e!r}"
                    ) from e
                raise
        self._logged_in = True

    def _logged_in_session(self) -> aiohttp.ClientSession:
        if not self._logged_in:
            raise AuthenticationError("The Hammerspace API session is not logged in.")
        return self._session

    async def _check_nfs_export(self, export_path: str) -> None:
        host = self._address.host
        if host is None:
            log.warning(
                "invalid host in address, skipping NFS export check",
                address=str(self._address),
            )
            return
        count = NFS_CHECK_RETRY_COUNT
        while count > 0:
            count -= 1
            try:
                await check_nfs_remote_server(host, export_path)
            except ShowmountNotFound:
                log.warning("showmount command not found, install the nfs-common package")
                return
            except ExportPathNotFound:
                log.debug(
                    "NFS export path {} not found on the server {}. Retrying...", export_path, host
                )
            except BaseNFSMountCheckFailed:
                log.warning(
                    "NFS export check failed, retrying",
                    exc_info=True,
                    export_path=export_path,
                    host=host,
                )
            else:
                log.debug("Found NFS export {} on the server {}", export_path, host)
                return
            await asyncio.sleep(NFS_CHECK_WAIT_SEC)
        log.error("NFS export verification failed", export_path=export_path, host=host)

    async def create_share(
        self,
        request: HammerspaceCreateShareRequest,
        retry: int,
        wait_sec: int,
        *,
        create_path: bool = True,
        validate_only: bool = False,
    ) -> SimpleShare:
        session = self._logged_in_session()
        query = HammerspaceCreateShareQuery(
            create_path="true" if create_path else "false",
            validate_only="true" if validate_only else "false",
        )
        async with session.post(
            self._address / "shares",
            params=query.model_dump(mode="json", by_alias=True),
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
            ssl=self._ssl_enabled,
        ) as resp:
            resp.raise_for_status()

        while retry > 0:
            log.debug(
                "Retrying to get the created share: {}, remaining retries: {}", request.name, retry
            )
            raw_shares = await self._get_shares(request.name)
            for raw_share in raw_shares:
                try:
                    share = SimpleShare.model_validate(raw_share)
                    if share.name == request.name:
                        await self._check_nfs_export(share.path)
                        return share
                except BackendAISchemaValidationFailed:
                    continue
            retry -= 1
            await asyncio.sleep(wait_sec)
        raise ShareNotFound(f"Failed to get the created share: {request.name}")

    async def _get_shares(self, name: str) -> list[dict[str, Any]]:
        session = self._logged_in_session()
        query = HammerspaceGetShareQuery(spec=f"name=eq={name}")
        async with session.get(
            self._address / "shares",
            params=query.model_dump(mode="json", by_alias=True),
            ssl=self._ssl_enabled,
        ) as resp:
            resp.raise_for_status()
            return cast(list[dict[str, Any]], await resp.json())

    async def get_share(self, name: str) -> Share | None:
        data = await self._get_shares(name)
        for raw_share in data:
            try:
                share = Share.model_validate(raw_share)
                if share.name == name:
                    return share
            except BackendAISchemaValidationFailed:
                continue
        return None

    async def poll_share(
        self,
        name: str,
        retry: int,
        wait_sec: int,
    ) -> Share | None:
        while retry > 0:
            data = await self._get_shares(name)
            for raw_share in data:
                try:
                    share = Share.model_validate(raw_share)
                except BackendAISchemaValidationFailed:
                    continue
                if share.name == name:
                    return share
            retry -= 1
            await asyncio.sleep(wait_sec)
        return None

    async def get_objective(self, id: uuid.UUID) -> Objective | None:
        session = self._logged_in_session()
        query = HammerspaceGetObjectiveQuery(spec=f"uoid.uuid=eq={id}")
        async with session.get(
            self._address / "objectives", params=query.model_dump(mode="json", by_alias=True)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        objectives = [Objective.model_validate(obj) for obj in data]
        for obj in objectives:
            if obj.uoid.uuid == id:
                return obj
        return None

    async def get_sites(self) -> list[Site]:
        session = self._logged_in_session()
        async with session.get(self._address / "sites") as resp:
            resp.raise_for_status()
            data = await resp.json()
        sites: list[Site] = []
        for s in data:
            try:
                sites.append(Site.model_validate(s))
            except BackendAISchemaValidationFailed:
                log.warning("site data parse failed", exc_info=True, site_data=str(s))
                continue
        return sites

    async def get_cluster_metrics(
        self,
        site_id: uuid.UUID,
        preceding_duration: str,
        interval_duration: str,
        object_type: ObjectType = ObjectType.CLUSTER,
    ) -> Metric:
        session = self._logged_in_session()
        query = HammerspaceClusterMetricQuery(
            precedingDuration=preceding_duration,
            intervalDuration=interval_duration,
        )
        async with session.get(
            self._address / f"metrics/capacity/{object_type}/{site_id}",
            params=query.model_dump(mode="json", by_alias=True),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return Metric.model_validate(data)

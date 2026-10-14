from __future__ import annotations

import ssl
import time
import urllib.parse
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

import aiohttp
from aiohttp import web

from ai.backend.common.clients.storage_backends.weka.dto import (
    WekaClusterInfo,
    WekaFs,
    WekaGetMetricQuery,
    WekaLoginRequest,
    WekaMetrics,
    WekaQuota,
    WekaRefreshLoginRequest,
    WekaSetQuotaRequest,
    WekaSetQuotaV1Params,
    WekaSetQuotaV1Request,
)
from ai.backend.common.clients.storage_backends.weka.exceptions import (
    WekaAPIError,
    WekaInvalidBodyError,
    WekaNotFoundError,
    WekaUnauthorizedError,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import BinarySize

_SUPPORTED_METHODS: Final = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


def error_handler[**P, R](inner: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    async def outer(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await inner(*args, **kwargs)
        except web.HTTPBadRequest as e:
            raise WekaInvalidBodyError from e
        except web.HTTPNotFound as e:
            raise WekaNotFoundError from e

    return outer


@dataclass
class WekaAPIClientArgs:
    endpoint: str
    username: str
    password: str
    organization: str
    ssl_context: ssl.SSLContext | bool = False


class WekaAPIClient:
    """Weka REST API client.

    The caller logs in with ``login()`` whenever ``is_logged_in`` is false.
    """

    _api_endpoint: str
    _username: str
    _password: str
    _organization: str
    _ssl_context: ssl.SSLContext | bool
    _access_token: str | None
    _refresh_token: str | None
    _valid_until: float
    _session: aiohttp.ClientSession

    def __init__(self, args: WekaAPIClientArgs) -> None:
        self._api_endpoint = args.endpoint
        self._username = args.username
        self._password = args.password
        self._organization = args.organization
        self._ssl_context = args.ssl_context
        self._access_token = None
        self._refresh_token = None
        self._valid_until = 0.0
        self._session = aiohttp.ClientSession(base_url=self._api_endpoint)

    async def aclose(self) -> None:
        await self._session.close()

    @property
    def is_logged_in(self) -> bool:
        return self._access_token is not None and self._valid_until >= time.time()

    async def login(self) -> None:
        if self._refresh_token is not None:
            response = await self._session.post(
                "/api/v2/login/refresh",
                data=WekaRefreshLoginRequest(refresh_token=self._refresh_token).model_dump(
                    mode="json", by_alias=True
                ),
                ssl=self._ssl_context,
            )
        else:
            response = await self._session.post(
                "/api/v2/login",
                data=WekaLoginRequest(
                    username=self._username,
                    password=self._password,
                    org=self._organization,
                ).model_dump(mode="json", by_alias=True),
                ssl=self._ssl_context,
            )
        async with response:
            data = await response.json()
        self._access_token = data["data"]["access_token"]
        self._refresh_token = data["data"]["refresh_token"]
        self._valid_until = data["data"]["expires_in"] + time.time()

    def _req_header(self) -> dict[str, str]:
        if not self.is_logged_in:
            raise WekaUnauthorizedError("The access token for Weka API is not valid.")
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        if method not in _SUPPORTED_METHODS:
            raise WekaAPIError(f"Unsupported request method {method}")
        try:
            response = await self._session.request(
                method,
                "/api/v2" + path,
                headers=self._req_header(),
                json=body,
                ssl=self._ssl_context,
            )
        except web.HTTPUnauthorized as e:
            raise WekaUnauthorizedError from e
        async with response:
            yield response

    @error_handler
    async def list_fs(self) -> Iterable[WekaFs]:
        async with self._request("GET", "/fileSystems") as response:
            data = await response.json()
        if len(data["data"]) == 0:
            raise WekaNotFoundError
        return [WekaFs.model_validate(fs_json) for fs_json in data["data"]]

    @error_handler
    async def get_fs(self, fs_uid: str) -> WekaFs:
        async with self._request("GET", f"/fileSystems/{fs_uid}") as response:
            data = await response.json()
        if data.get("data") is None:
            raise WekaNotFoundError
        return WekaFs.model_validate(data["data"])

    @error_handler
    async def list_quotas(self, fs_uid: str) -> Iterable[WekaQuota]:
        async with self._request("GET", f"/fileSystems/{fs_uid}/quota") as response:
            data = await response.json()
        if isinstance(data["data"], list):
            return [
                WekaQuota.from_api(quota_info["quota_id"], quota_info)
                for quota_info in data["data"]
            ]
        return [
            WekaQuota.from_api(quota_id, data["data"][quota_id]) for quota_id in data["data"].keys()
        ]

    @error_handler
    async def get_quota(self, fs_uid: str, inode_id: int) -> WekaQuota:
        async with self._request("GET", f"/fileSystems/{fs_uid}/quota/{inode_id}") as response:
            data = await response.json()
        if data.get("message") == "Directory has no quota" or len(data["data"].keys()) == 0:
            raise WekaNotFoundError
        if "inode_id" in data["data"]:
            return WekaQuota.from_api("", data["data"])
        quota_id = list(data["data"].keys())[0]
        return WekaQuota.from_api(quota_id, data["data"][quota_id])

    @error_handler
    async def set_quota(
        self,
        fs_uid: str,
        inode_id: int,
        soft_limit: BinarySize,
        hard_limit: BinarySize,
    ) -> WekaQuota:
        def _format_size(s: BinarySize) -> str:
            ss = str(s)
            if ss.endswith("bytes"):
                return ss.replace("bytes", "B").replace(" ", "")
            return ss.replace(" ", "")

        body = WekaSetQuotaRequest(
            grace_seconds=None,
            soft_limit_bytes=_format_size(soft_limit),
            hard_limit_bytes=_format_size(hard_limit),
        ).model_dump(mode="json", by_alias=True)
        async with self._request(
            "PUT", f"/fileSystems/{fs_uid}/quota/{inode_id}", body
        ) as response:
            data = await response.json()
        quota_id = list(data["data"].keys())[0]
        return WekaQuota.from_api(quota_id, data["data"][quota_id])

    @error_handler
    async def set_quota_v1(
        self,
        path: str,
        inode_id: int,
        hard_limit: int | None = None,
        soft_limit: int | None = None,
    ) -> None:
        """Sets quota using the undocumented V1 API."""
        body = WekaSetQuotaV1Request(
            id=time.time() * 1000,
            params=WekaSetQuotaV1Params(
                inode_context=inode_id,
                path=path,
                soft_limit_bytes=soft_limit,
                hard_limit_bytes=hard_limit,
            ),
        ).model_dump(mode="json", by_alias=True, exclude_none=True)
        async with self._session.post(
            self._api_endpoint + "/api/v1",
            headers=self._req_header(),
            data=dump_json_str(body),
            ssl=self._ssl_context,
        ):
            pass

    @error_handler
    async def remove_quota(self, fs_uid: str, inode_id: int) -> None:
        async with self._request("DELETE", f"/fileSystems/{fs_uid}/quota/{inode_id}"):
            pass

    @error_handler
    async def check_health(self) -> str:
        async with self._request("GET", "/healthcheck") as response:
            return await response.text()

    @error_handler
    async def get_cluster_info(self) -> WekaClusterInfo:
        async with self._request("GET", "/cluster") as response:
            data = await response.json()
        return WekaClusterInfo.model_validate(data["data"])

    @error_handler
    async def get_metric(
        self,
        metrics: Iterable[str],
        start_time: datetime,
        end_time: datetime | None = None,
        category: str | None = None,
    ) -> WekaMetrics:
        query = WekaGetMetricQuery(
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z" if end_time is not None else None,
            category=category,
            stat=list(metrics),
        )
        querystring = urllib.parse.urlencode(
            query.model_dump(mode="json", by_alias=True, exclude_none=True), doseq=True
        )
        async with self._request("GET", f"/stats?{querystring}") as response:
            data = await response.json()
        return WekaMetrics.model_validate({"categories": data["data"]["all"]})

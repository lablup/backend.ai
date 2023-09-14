from __future__ import annotations

import logging
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping, NewType, TypedDict

import aiohttp
from yarl import URL

from ai.backend.common.logging import BraceStyleAdapter

from ..types import CapacityUsage
from .config import APIVersion
from .exceptions import (
    VastAPIError,
    VastInvalidParameterError,
    VastNotFoundError,
    VastUnauthorizedError,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


DEFAULT_ACCESS_TOKEN_SPAN: Final = timedelta(hours=1)
DEFAULT_REFRESH_TOKEN_SPAN: Final = timedelta(hours=24)


VastQuotaID = NewType("VastQuotaID", str)


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


GET = RequestMethod.GET
POST = RequestMethod.GET
PATCH = RequestMethod.GET
DELETE = RequestMethod.GET


class TokenData(TypedDict):
    token: str
    issued_dt: datetime


class TokenPair(TypedDict):
    access_token: TokenData
    refresh_token: TokenData


class Performance(TypedDict):
    read_bw: int
    read_iops: int
    write_bw: float
    write_iops: int


def default_perf() -> Performance:
    return {"read_bw": -1, "read_iops": -1, "write_bw": -1, "write_iops": -1}


@dataclass(match_args=True)
class VastClusterInfo:
    id: str
    guid: str
    ip: str
    mgmt_vip: str
    name: str
    state: str
    physical_space: int = -1
    physical_space_in_use: int = -1
    usable_capacity_bytes: int = -1
    iops: int = -1
    rd_iops: int = -1
    wr_iops: int = -1
    bw: int = -1  # Bandwidth
    rd_bw: int = -1
    wr_bw: int = -1
    latency: int = -1
    rd_latency: int = -1
    wr_latency: int = -1
    max_file_size: int = -1
    max_performance: Performance = field(default_factory=default_perf)

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> VastClusterInfo:
        return VastClusterInfo(**{arg: obj.get(arg) for arg in cls.__match_args__})  # type: ignore[arg-type]


@dataclass(match_args=True)
class VastQuota:
    path: str
    id: VastQuotaID
    guid: str
    name: str
    state: str
    grace_period: str
    soft_limit: int
    hard_limit: int
    soft_limit_inodes: int
    hard_limit_inodes: int
    used_inodes: int
    used_capacity: int
    percent_capacity: int

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> VastQuota:
        return VastQuota(**{arg: obj.get(arg) for arg in cls.__match_args__})  # type: ignore[arg-type]


class VastAPIClient:
    api_endpoint: URL
    username: str
    password: str
    ssl_context: ssl.SSLContext | bool | None

    _auth_token: TokenPair | None

    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        *,
        api_version: APIVersion,
        ssl: ssl.SSLContext | bool | None = None,
    ) -> None:
        self.api_endpoint = URL(endpoint) / "api" / str(api_version)
        self.username = username
        self.password = password

        self._auth_token = None
        self.ssl_context = ssl

    @property
    def _req_header(self) -> Mapping[str, str]:
        assert self._auth_token is not None
        return {
            "Authorization": f"Bearer {self._auth_token['access_token']['token']}",
            "Content-Type": "application/json",
        }

    async def _validate_token(self, sess: aiohttp.ClientSession) -> None:
        current_dt = datetime.now()
        if self._auth_token is None:
            return await self._login(sess)
        elif self._auth_token["access_token"]["issued_dt"] + DEFAULT_ACCESS_TOKEN_SPAN > current_dt:
            return
        elif (
            self._auth_token["refresh_token"]["issued_dt"] + DEFAULT_REFRESH_TOKEN_SPAN > current_dt
        ):
            return await self._refresh(sess)
        return await self._login(sess)

    def _parse_token(self, data: Mapping[str, Any]) -> None:
        current_dt = datetime.now()
        access_token = TokenData(token=data["access"], issued_dt=current_dt)
        refresh_token = TokenData(token=data["refresh"], issued_dt=current_dt)
        self._auth_token = TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def _refresh(self, sess: aiohttp.ClientSession) -> None:
        if self._auth_token is None:
            raise VastUnauthorizedError("Cannot refresh without refresh token.")
        response = await sess.post(
            "/api/token/refresh",
            data={"refresh_token": self._auth_token["refresh_token"]["token"]},
            ssl=self.ssl_context,
        )
        data = await response.json()
        self._parse_token(data)

    async def _login(self, sess: aiohttp.ClientSession) -> None:
        response = await sess.post(
            "/api/token",
            data={
                "username": self.username,
                "password": self.password,
            },
            ssl=self.ssl_context,
        )
        data = await response.json()
        self._parse_token(data)

    async def _build_request(
        self,
        sess: aiohttp.ClientSession,
        method: RequestMethod,
        path: str,
        body: Mapping[str, Any] | None = None,
    ) -> aiohttp.ClientResponse:
        await self._validate_token(sess)

        match method:
            case RequestMethod.GET:
                func = sess.get
            case RequestMethod.POST:
                func = sess.post
            case RequestMethod.PATCH:
                func = sess.patch
            case RequestMethod.DELETE:
                func = sess.delete
            case _:
                raise VastAPIError(f"Unsupported request method {method}")

        return await func(path, headers=self._req_header, json=body, ssl=self.ssl_context)

    async def list_quotas(self) -> list[VastQuota]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                GET,
                "/quotas/",
            )
            data: list[Mapping[str, Any]] = await response.json()
        return [VastQuota.from_json(info) for info in data]

    async def get_quota(self, vast_quota_id: VastQuotaID) -> VastQuota:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                GET,
                f"/quotas/{str(vast_quota_id)}/",
            )
            if response.status == 404:
                raise VastNotFoundError
            data: Mapping[str, Any] = await response.json()
        if data.get("detail") == "Not found." or "id" not in data:
            raise VastNotFoundError

        return VastQuota.from_json(data)

    async def set_quota(
        self,
        path: Path,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> VastQuota:
        body: dict[str, Any] = {"path": path}
        if soft_limit is not None:
            body["soft_limit"] = soft_limit
        if hard_limit is not None:
            body["hard_limit"] = hard_limit
        if soft_limit_inodes is not None:
            body["soft_limit_inodes"] = soft_limit_inodes
        if hard_limit_inodes is not None:
            body["hard_limit_inodes"] = hard_limit_inodes
        if grace_period is not None:
            body["grace_period"] = grace_period

        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                POST,
                "/quotas/",
                body,
            )
            data: Mapping[str, Any] = await response.json()
            match response.status // 100:
                case 2:
                    pass
                case 4 | 5:
                    err_msg = data.get("detail", "Unkown error from vast API")
                    raise VastInvalidParameterError(err_msg)
                case _:
                    raise VastInvalidParameterError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )
        return VastQuota.from_json(data)

    async def modify_quota(
        self,
        vast_quota_id: VastQuotaID,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> None:
        body: dict[str, Any] = {}
        if soft_limit is not None:
            body["soft_limit"] = soft_limit
        if hard_limit is not None:
            body["hard_limit"] = hard_limit
        if soft_limit_inodes is not None:
            body["soft_limit_inodes"] = soft_limit_inodes
        if hard_limit_inodes is not None:
            body["hard_limit_inodes"] = hard_limit_inodes
        if grace_period is not None:
            body["grace_period"] = grace_period

        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                PATCH,
                f"/quotas/{vast_quota_id}/",
                body,
            )
            data: Mapping[str, Any] = await response.json()
            match response.status // 100:
                case 2:
                    pass
                case 4 | 5:
                    err_msg = data.get("detail", "Unkown error from vast API")
                    raise VastInvalidParameterError(err_msg)
                case _:
                    raise VastInvalidParameterError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )

    async def remove_quota(self, vast_quota_id: VastQuotaID) -> None:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            await self._build_request(
                sess,
                DELETE,
                f"/quotas/{vast_quota_id}",
            )

    async def get_cluster_info(self) -> list[VastClusterInfo]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, GET, "/cluster/")
            data: list[Mapping[str, Any]] = await response.json()
            return [VastClusterInfo.from_json(info) for info in data]

    async def get_capacity_info(self) -> CapacityUsage:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, GET, "/capacity/")
            data: Mapping[str, Any] = await response.json()

        infos = data["details"]
        root_dir = "/"
        capacity_bytes, percent = None, None
        for path, info in infos:
            if path == root_dir:
                capacity_bytes = info["data"][0]
                percent = info["percent"]
        else:
            capacity_bytes = info["data"][0]
            percent = info["percent"]
        return CapacityUsage(
            capacity_bytes=capacity_bytes,
            used_bytes=(100 - percent) * capacity_bytes,
        )


# GET /capacity/
# {'details': [['/',
#               {'average_atime': '2023-09-12 09:37',
#                'data': [860139153249, 851767474592, 1054220763504],
#                'parent': '/',
#                'percent': 100}],
#              ['/vast',
#               {'average_atime': '2023-09-12 09:37',
#                'data': [860139153249, 851767474592, 1054220763504],
#                'parent': '/',
#                'percent': 100.0}],
#              ['/vast/gds',
#               {'average_atime': '2023-09-12 09:37',
#                'data': [860139153249, 851767474592, 1054220763504],
#                'parent': '/vast',
#                'percent': 100.0}]],
#  'keys': ['usable', 'unique', 'logical'],
#  'root_data': [860407183894, 851249021799, 1055847071418],
#  'small_folders': [['/test-quota-dir',
#                     {'average_atime': None,
#                      'data': [0, 0, 0],
#                      'parent': '/',
#                      'percent': 0}]],
#  'sort_key': 'usable',
#  'time': '2023-09-14 18:02:44'}


# qospolicies
# Quality of Service policies enable you to define quality of service per view.
# Quality of service policies can set maximum limits on read and write bandwidth and IOPS per view.

# GET /qospolicies/
# []

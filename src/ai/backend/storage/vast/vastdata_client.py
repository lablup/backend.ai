from __future__ import annotations

import logging
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping, NewType, TypedDict

import aiohttp
import jwt
from yarl import URL

from ai.backend.common.logging import BraceStyleAdapter

from ..exception import ExternalError, QuotaScopeAlreadyExists
from ..types import CapacityUsage
from .config import APIVersion
from .exceptions import (
    VASTAPIError,
    VASTInvalidParameterError,
    VASTNotFoundError,
    VASTUnauthorizedError,
    VASTUnknownError,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


DEFAULT_ACCESS_TOKEN_SPAN: Final = timedelta(hours=1)
DEFAULT_REFRESH_TOKEN_SPAN: Final = timedelta(hours=24)


VASTQuotaID = NewType("VASTQuotaID", str)


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


GET = RequestMethod.GET
POST = RequestMethod.POST
PATCH = RequestMethod.PATCH
DELETE = RequestMethod.DELETE


class TokenPair(TypedDict):
    access_token: str
    refresh_token: str


class Performance(TypedDict):
    read_bw: int
    read_iops: int
    write_bw: float
    write_iops: int


def default_perf() -> Performance:
    return {"read_bw": -1, "read_iops": -1, "write_bw": -1, "write_iops": -1}


@dataclass
class VASTClusterInfo:
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
    def from_json(cls, obj: Mapping[str, Any]) -> VASTClusterInfo:
        return VASTClusterInfo(**obj)


@dataclass
class VASTQuota:
    path: str
    id: VASTQuotaID
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
    def from_json(cls, obj: Mapping[str, Any]) -> VASTQuota:
        return VASTQuota(**obj)


@dataclass
class Cache:
    cluster_info: VASTClusterInfo | None


class VASTAPIClient:
    api_endpoint: URL
    api_version: APIVersion
    username: str
    password: str
    ssl_context: ssl.SSLContext | bool | None
    storage_base_dir: Path
    cache: Cache

    _auth_token: TokenPair | None

    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        *,
        api_version: APIVersion,
        storage_base_dir: str,
        ssl: ssl.SSLContext | bool | None = None,
    ) -> None:
        self.api_endpoint = URL(endpoint)
        self.api_version = api_version
        self.username = username
        self.password = password
        self.storage_base_dir = Path(storage_base_dir)
        self.cache = Cache(cluster_info=None)

        self._auth_token = None
        self.ssl_context = ssl

    @property
    def _req_header(self) -> Mapping[str, str]:
        assert self._auth_token is not None
        return {
            "Authorization": f"Bearer {self._auth_token['access_token']}",
            "Content-Type": "application/json",
        }

    async def _validate_token(self) -> None:
        current_dt = datetime.now()

        def get_exp_dt(token: str) -> datetime:
            decoded: Mapping[str, Any] = jwt.decode(
                token,
                algorithms=["HS256"],
                options={
                    "verify_signature": False,
                },
            )
            return datetime.fromtimestamp(decoded["exp"])

        if self._auth_token is None:
            return await self._login()
        elif get_exp_dt(self._auth_token["access_token"]) + DEFAULT_ACCESS_TOKEN_SPAN > current_dt:
            return
        elif (
            get_exp_dt(self._auth_token["refresh_token"]) + DEFAULT_REFRESH_TOKEN_SPAN > current_dt
        ):
            return await self._refresh()
        return await self._login()

    def _parse_token(self, data: Mapping[str, Any]) -> None:
        self._auth_token = TokenPair(access_token=data["access"], refresh_token=data["refresh"])

    async def _refresh(self) -> None:
        if self._auth_token is None:
            raise VASTUnauthorizedError("Cannot refresh without refresh token.")
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await sess.post(
                f"/api/{str(self.api_version)}/token/refresh/",
                headers={
                    "Accept": "*/*",
                },
                data={"refresh_token": self._auth_token["refresh_token"]},
                ssl=self.ssl_context,
            )
        data = await response.json()
        self._parse_token(data)

    async def _login(self) -> None:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await sess.post(
                f"/api/{str(self.api_version)}/token/",
                headers={
                    "Accept": "*/*",
                },
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
        await self._validate_token()

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
                raise VASTAPIError(f"Unsupported request method {method}")

        real_rel_path = URL("/api/") / str(self.api_version) / path
        return await func(real_rel_path, headers=self._req_header, json=body, ssl=self.ssl_context)

    async def list_quotas(self) -> list[VASTQuota]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                GET,
                "quotas/",
            )
            data: list[Mapping[str, Any]] = await response.json()
        return [VASTQuota.from_json(info) for info in data]

    async def get_quota(self, vast_quota_id: VASTQuotaID) -> VASTQuota | None:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                GET,
                f"quotas/{str(vast_quota_id)}/",
            )
            if response.status == 404:
                return None
            data: Mapping[str, Any] = await response.json()
        if data.get("detail") == "Not found." or "id" not in data:
            return None

        return VASTQuota.from_json(data)

    async def set_quota(
        self,
        path: Path,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> VASTQuota:
        body: dict[str, Any] = {
            "name": str(path),
            "path": str(self.storage_base_dir / path.name),
            "create_dir": False,  # Explicitly disable to create directory owned by root.
        }
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
                "quotas/",
                body,
            )
            data: Mapping[str, Any] = await response.json()
            match response.status:
                case 201 | 200:
                    pass
                case 400 | 401:
                    raise VASTInvalidParameterError
                case 403:
                    raise VASTUnauthorizedError
                case 503:
                    raise QuotaScopeAlreadyExists
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )
        return VASTQuota.from_json(data)

    async def modify_quota(
        self,
        vast_quota_id: VASTQuotaID,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> VASTQuota:
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
                f"quotas/{vast_quota_id}/",
                body,
            )
            data: Mapping[str, Any] = await response.json()
            match response.status // 100:
                case 2:
                    pass
                case 4:
                    err_msg = data.get("detail", "Invalid parameter")
                    raise VASTInvalidParameterError(err_msg)
                case 5:
                    err_msg = data.get("detail", "VAST server error")
                    raise VASTUnknownError(err_msg)
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )
        return VASTQuota.from_json(data)

    async def remove_quota(self, vast_quota_id: VASTQuotaID) -> None:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                DELETE,
                f"quotas/{vast_quota_id}/",
            )
            if response.status == 404:
                raise VASTNotFoundError

    async def get_cluster_info(self, cluster_id: int) -> VASTClusterInfo | None:
        if (_cached := self.cache.cluster_info) is not None:
            return _cached
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, GET, f"clusters/{cluster_id}/")
            match response.status:
                case 200:
                    data: Mapping[str, Any] = await response.json()
                    result = VASTClusterInfo.from_json(data)
                    self.cache.cluster_info = result
                    return result
                case 404:
                    return None
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )

    async def get_capacity_info(self) -> CapacityUsage:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, GET, "capacity/")
            data: Mapping[str, Any] = await response.json()

        def _parse(detail_info: Mapping[str, Any]) -> CapacityUsage:
            usable, unique, logical = detail_info["data"]
            capacity_bytes = usable
            usable_percent = detail_info["percent"]
            return CapacityUsage(
                capacity_bytes=capacity_bytes,
                used_bytes=int((100 - usable_percent) * capacity_bytes),
            )

        infos = data["details"]
        root_dir = "/"
        for path, info in infos:
            if path == root_dir:
                return _parse(info)
        raise ExternalError("No capacity data found from vast API")


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

from __future__ import annotations

import enum
import logging
import ssl
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

import aiohttp
import jwt
from yarl import URL

from ai.backend.common.clients.storage_backends.vast.dto import (
    APIVersion,
    VASTCapacityUsage,
    VASTClusterInfo,
    VASTListQuotasQuery,
    VASTLoginRequest,
    VASTModifyQuotaRequest,
    VASTQuota,
    VASTQuotaID,
    VASTRefreshTokenRequest,
    VASTSetQuotaRequest,
    VASTTokenPair,
)
from ai.backend.common.clients.storage_backends.vast.exceptions import (
    VASTAPIError,
    VASTCapacityNotFoundError,
    VASTInvalidParameterError,
    VASTNotFoundError,
    VASTQuotaAlreadyExistsError,
    VASTUnauthorizedError,
    VASTUnknownError,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

TOKEN_EXPIRATION_BUFFER: Final = timedelta(minutes=1)


class RequestMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class _ClusterInfoCache:
    cluster_info: VASTClusterInfo
    timestamp: float


@dataclass
class VASTAPIClientArgs:
    endpoint: str
    username: str
    password: str
    api_version: APIVersion
    storage_base_dir: str
    cluster_info_cache_ttl: float
    ssl_context: ssl.SSLContext | bool = False
    force_login: bool = True


def _get_exp_dt(token: str) -> datetime:
    decoded: dict[str, Any] = jwt.decode(
        token,
        algorithms=["HS256"],
        options={"verify_signature": False},
    )
    return datetime.fromtimestamp(decoded["exp"], tz=UTC)


class VASTAPIClient:
    """VAST REST API client.

    The caller logs in with ``login()`` whenever ``is_logged_in`` is false.
    """

    _api_endpoint: URL
    _api_version: APIVersion
    _username: str
    _password: str
    _ssl_context: ssl.SSLContext | bool
    _storage_base_dir: Path
    _force_login: bool
    _cache_ttl: float
    _cache: _ClusterInfoCache | None
    _auth_token: VASTTokenPair | None
    _session: aiohttp.ClientSession

    def __init__(self, args: VASTAPIClientArgs) -> None:
        self._api_endpoint = URL(args.endpoint)
        self._api_version = args.api_version
        self._username = args.username
        self._password = args.password
        self._ssl_context = args.ssl_context
        self._storage_base_dir = Path(args.storage_base_dir)
        self._force_login = args.force_login
        self._cache_ttl = args.cluster_info_cache_ttl
        self._cache = None
        self._auth_token = None
        self._session = aiohttp.ClientSession(base_url=self._api_endpoint)

    async def aclose(self) -> None:
        await self._session.close()

    @property
    def is_logged_in(self) -> bool:
        if self._auth_token is None:
            return False
        current_dt = datetime.now(UTC)
        return _get_exp_dt(self._auth_token.access_token) > current_dt + TOKEN_EXPIRATION_BUFFER

    async def login(self) -> None:
        """Refreshes or reissues the tokens; ``force_login`` always reissues them."""
        if self._force_login or self._auth_token is None:
            return await self._login()
        current_dt = datetime.now(UTC)
        if _get_exp_dt(self._auth_token.access_token) > current_dt + TOKEN_EXPIRATION_BUFFER:
            return None
        if _get_exp_dt(self._auth_token.refresh_token) > current_dt + TOKEN_EXPIRATION_BUFFER:
            return await self._refresh()
        return await self._login()

    def _parse_token(self, data: dict[str, Any]) -> None:
        try:
            self._auth_token = VASTTokenPair(
                access_token=data["access"], refresh_token=data["refresh"]
            )
        except KeyError as e:
            raise VASTAPIError(f"Cannot parse token with given data (d:{data!s})") from e

    async def _refresh(self) -> None:
        if self._auth_token is None:
            raise VASTUnauthorizedError("Cannot refresh without refresh token.")
        async with self._session.post(
            f"/api/{self._api_version!s}/token/refresh/",
            headers={"Accept": "*/*"},
            data=VASTRefreshTokenRequest(refresh_token=self._auth_token.refresh_token).model_dump(
                mode="json", by_alias=True
            ),
            ssl=self._ssl_context,
        ) as response:
            data = await response.json()
        self._parse_token(data)

    async def _login(self) -> None:
        async with self._session.post(
            f"/api/{self._api_version!s}/token/",
            headers={"Accept": "*/*"},
            data=VASTLoginRequest(username=self._username, password=self._password).model_dump(
                mode="json", by_alias=True
            ),
            ssl=self._ssl_context,
        ) as response:
            data = await response.json()
        self._parse_token(data)

    def _req_header(self) -> dict[str, str]:
        if self._auth_token is None or not self.is_logged_in:
            raise VASTUnauthorizedError("The access token for VAST API is not valid.")
        return {
            "Authorization": f"Bearer {self._auth_token.access_token}",
            "Content-Type": "application/json",
        }

    @asynccontextmanager
    async def _request(
        self,
        method: RequestMethod,
        path: str,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        real_rel_path = URL("/api/") / str(self._api_version) / path
        async with self._session.request(
            method.value,
            real_rel_path,
            headers=self._req_header(),
            json=body,
            params=params,
            ssl=self._ssl_context,
        ) as response:
            yield response

    async def list_quotas(self, qname: str | None = None) -> list[VASTQuota]:
        params = VASTListQuotasQuery(name=qname).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
        async with self._request(RequestMethod.GET, "quotas/", params=params) as response:
            data: list[dict[str, Any]] = await response.json()
        return [VASTQuota.model_validate(info) for info in data]

    async def get_quota(self, vast_quota_id: VASTQuotaID) -> VASTQuota | None:
        async with self._request(RequestMethod.GET, f"quotas/{vast_quota_id!s}/") as response:
            if response.status == 404:
                return None
            data: dict[str, Any] = await response.json()
        if data.get("detail") == "Not found." or "id" not in data:
            return None
        return VASTQuota.model_validate(data)

    async def set_quota(
        self,
        path: Path,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> VASTQuota:
        body = VASTSetQuotaRequest(
            name=str(path),
            path=str(self._storage_base_dir / path.name),
            create_dir=False,
            soft_limit=soft_limit,
            hard_limit=hard_limit,
            soft_limit_inodes=soft_limit_inodes,
            hard_limit_inodes=hard_limit_inodes,
            grace_period=grace_period,
        ).model_dump(mode="json", by_alias=True, exclude_none=True)

        async with self._request(RequestMethod.POST, "quotas/", body) as response:
            data: dict[str, Any] = await response.json()
            match response.status:
                case 201 | 200:
                    pass
                case 400 | 401:
                    raise VASTInvalidParameterError(f"Invalid parameter (data:{data!s})")
                case 403:
                    raise VASTUnauthorizedError
                case 503:
                    raise VASTQuotaAlreadyExistsError
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )
        return VASTQuota.model_validate(data)

    async def modify_quota(
        self,
        vast_quota_id: VASTQuotaID,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        soft_limit_inodes: int | None = None,
        hard_limit_inodes: int | None = None,
        grace_period: str | None = None,
    ) -> VASTQuota:
        body = VASTModifyQuotaRequest(
            soft_limit=soft_limit,
            hard_limit=hard_limit,
            soft_limit_inodes=soft_limit_inodes,
            hard_limit_inodes=hard_limit_inodes,
            grace_period=grace_period,
        ).model_dump(mode="json", by_alias=True, exclude_none=True)

        async with self._request(RequestMethod.PATCH, f"quotas/{vast_quota_id}/", body) as response:
            data: dict[str, Any] = await response.json()
            match response.status // 100:
                case 2:
                    pass
                case 4:
                    raise VASTInvalidParameterError(f"Invalid parameter (data:{data!s})")
                case 5:
                    raise VASTUnknownError(data.get("detail", "VAST server error"))
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )
        return VASTQuota.model_validate(data)

    async def remove_quota(self, vast_quota_id: VASTQuotaID) -> None:
        async with self._request(RequestMethod.DELETE, f"quotas/{vast_quota_id}/") as response:
            if response.status == 404:
                raise VASTNotFoundError

    async def get_cluster_info(self, cluster_id: int) -> VASTClusterInfo | None:
        current_time = time.time()
        if (cached := self._cache) is not None:
            if current_time - cached.timestamp < self._cache_ttl:
                return cached.cluster_info
        async with self._request(RequestMethod.GET, f"clusters/{cluster_id}/") as response:
            match response.status:
                case 200:
                    data: dict[str, Any] = await response.json()
                    result = VASTClusterInfo.model_validate(data)
                    self._cache = _ClusterInfoCache(cluster_info=result, timestamp=current_time)
                    return result
                case 404:
                    log.warning("VAST cluster not found", cluster_id=str(cluster_id))
                    return None
                case _:
                    raise VASTUnknownError(
                        f"Unkwon error from vast API. status code: {response.status}"
                    )

    async def get_capacity_info(self) -> VASTCapacityUsage:
        async with self._request(RequestMethod.GET, "capacity/") as response:
            data: dict[str, Any] = await response.json()
        root_dir = "/"
        for path, info in data["details"]:
            if path == root_dir:
                capacity_bytes, _unique, _logical = info["data"]
                return VASTCapacityUsage(
                    capacity_bytes=capacity_bytes,
                    used_bytes=int((100 - info["percent"]) * capacity_bytes),
                )
        raise VASTCapacityNotFoundError(
            f"No capacity data found for root directory '{root_dir}' from VAST API"
        )

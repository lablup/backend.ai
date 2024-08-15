import json
import logging
import ssl
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import aiohttp
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize

from .exceptions import WekaAPIError, WekaInvalidBodyError, WekaNotFoundError, WekaUnauthorizedError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class WekaQuota:
    quota_id: str
    inode_id: int
    hard_limit: Optional[int]
    soft_limit: Optional[int]
    grace_seconds: Optional[int]
    used_bytes: Optional[int]

    @classmethod
    def from_json(cls, quota_id: str, data: Any):
        return WekaQuota(
            quota_id,
            data["inode_id"],
            data["hard_limit_bytes"],
            data["soft_limit_bytes"],
            data["grace_seconds"],
            data["used_bytes"],
        )

    def to_json(self):
        return {
            "quota_id": self.quota_id,
            "inode_id": self.inode_id,
            "hard_limit": self.hard_limit,
            "soft_limit": self.soft_limit,
            "grace_seconds": self.grace_seconds,
            "used_bytes": self.used_bytes,
        }


@dataclass
class WekaFs:
    id: str
    name: str
    uid: str
    group_id: str
    group_name: str
    used_total_data: int
    used_total: int
    free_total: int
    available_total: int
    available_ssd_metadata: int
    used_ssd: int
    free_ssd: int
    available_ssd: int
    ssd_budget: int
    total_budget: int

    def from_json(data: Any):
        return WekaFs(
            data["id"],
            data["name"],
            data["uid"],
            data["group_id"],
            data["group_name"],
            data["used_total_data"],
            data["used_total"],
            data["free_total"],
            data["available_total"],
            data["available_ssd_metadata"],
            data["used_ssd"],
            data["free_ssd"],
            data["available_ssd"],
            data["ssd_budget"],
            data["total_budget"],
        )


def error_handler(inner):
    async def outer(*args, **kwargs):
        try:
            return await inner(*args, **kwargs)
        except web.HTTPBadRequest:
            raise WekaInvalidBodyError
        except web.HTTPNotFound:
            raise WekaNotFoundError

    return outer


class WekaAPIClient:
    api_endpoint: str
    username: str
    password: str
    organization: str
    ssl_context: Optional[ssl.SSLContext | bool]

    _access_token: Optional[str]
    _refresh_token: Optional[str]
    _valid_until: int

    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        organization: str,
        ssl: Optional[ssl.SSLContext | bool] = None,
    ) -> None:
        self.api_endpoint = endpoint
        self.username = username
        self.password = password
        self.organization = organization

        self._access_token = None
        self._refresh_token = None
        self.ssl_context = ssl

    @property
    def _is_token_valid(self) -> bool:
        return self._access_token is not None and self._valid_until >= time.time()

    @property
    def _req_header(self) -> Mapping[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _login(self, sess: aiohttp.ClientSession) -> None:
        if self._refresh_token is not None:
            response = await sess.post(
                "/api/v2/login/refresh",
                data={"refresh_token": self._refresh_token},
                ssl=self.ssl_context,
            )
        else:
            response = await sess.post(
                "/api/v2/login",
                data={
                    "username": self.username,
                    "password": self.password,
                    "org": self.organization,
                },
                ssl=self.ssl_context,
            )
        data = await response.json()
        self._access_token = data["data"]["access_token"]
        self._refresh_token = data["data"]["refresh_token"]
        self._valid_until = data["data"]["expires_in"] + time.time()

    async def _build_request(
        self,
        sess: aiohttp.ClientSession,
        method: str,
        path: str,
        body: Optional[Any] = None,
    ) -> aiohttp.ClientResponse:
        match method:
            case "GET":
                func = sess.get
            case "POST":
                func = sess.post
            case "PUT":
                func = sess.put
            case "PATCH":
                func = sess.patch
            case "DELETE":
                func = sess.delete
            case _:
                raise WekaAPIError(f"Unsupported request method {method}")

        if not self._is_token_valid:
            await self._login(sess)

        try:
            if method == "GET" or method == "DELETE":
                return await func("/api/v2" + path, headers=self._req_header, ssl=self.ssl_context)
            else:
                return await func(
                    "/api/v2" + path, headers=self._req_header, json=body, ssl=self.ssl_context
                )
        except web.HTTPUnauthorized:
            await self._login(sess)
            try:
                if method == "GET" or method == "DELETE":
                    return await func(
                        "/api/v2" + path, headers=self._req_header, ssl=self.ssl_context
                    )

                else:
                    return await func(
                        "/api/v2" + path,
                        headers=self._req_header,
                        json=body,
                        ssl=self.ssl_context,
                    )

            except web.HTTPUnauthorized:
                raise WekaUnauthorizedError

    @error_handler
    async def list_fs(self) -> Iterable[WekaFs]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, "GET", "/fileSystems")
            data = await response.json()
        if len(data["data"]) == 0:
            raise WekaNotFoundError
        return [WekaFs.from_json(fs_json) for fs_json in data["data"]]

    @error_handler
    async def get_fs(self, fs_uid: str) -> WekaFs:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, "GET", f"/fileSystems/{fs_uid}")
            data = await response.json()
        if data.get("data") is None:
            raise WekaNotFoundError
        return WekaFs.from_json(data["data"])

    @error_handler
    async def list_quotas(self, fs_uid: str) -> Iterable[WekaQuota]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/fileSystems/{fs_uid}/quota",
            )
            data = await response.json()
        if isinstance(data["data"], list):
            return [
                WekaQuota.from_json(quota_info["quota_id"], quota_info)
                for quota_info in data["data"]
            ]
        else:
            return [
                WekaQuota.from_json(quota_id, data["data"][quota_id])
                for quota_id in data["data"].keys()
            ]

    @error_handler
    async def get_quota(self, fs_uid: str, inode_id: int) -> WekaQuota:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/fileSystems/{fs_uid}/quota/{inode_id}",
            )
            data = await response.json()
        if data.get("message") == "Directory has no quota" or len(data["data"].keys()) == 0:
            raise WekaNotFoundError
        if "inode_id" in data["data"]:
            return WekaQuota.from_json("", data["data"])
        else:
            quota_id = list(data["data"].keys())[0]
            return WekaQuota.from_json(quota_id, data["data"][quota_id])

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
            else:
                return ss.replace(" ", "")

        body = {
            "grace_seconds": None,
            "soft_limit_bytes": _format_size(soft_limit),
            "hard_limit_bytes": _format_size(hard_limit),
        }

        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                "PUT",
                f"/fileSystems/{fs_uid}/quota/{inode_id}",
                body,
            )
            data = await response.json()

        quota_id = data["data"].keys()[0]
        return WekaQuota(
            quota_id,
            data["data"][quota_id]["inode_id"],
            data["data"][quota_id]["hard_limit_bytes"],
            data["data"][quota_id]["soft_limit_bytes"],
            data["data"][quota_id]["grace_seconds"],
            data["data"][quota_id]["used_bytes"],
        )

    @error_handler
    async def set_quota_v1(
        self,
        path: str,
        inode_id: int,
        hard_limit: Optional[int] = None,
        soft_limit: Optional[int] = None,
    ) -> None:
        """
        Sets quota using undocumented V1 API. Should be considered deprecated
        after we figure out how to set limit as unlimited with V2 API.
        """
        body: MutableMapping[str, Any] = {
            "id": time.time() * 1000,
            "jsonrpc": "2.0",
            "method": "set_directory_quota",
            "params": {
                "activate": True,
                "inode_context": inode_id,
                "path": path,
            },
        }

        if soft_limit is not None:
            body["params"]["soft_limit_bytes"] = soft_limit
        if hard_limit is not None:
            body["params"]["hard_limit_bytes"] = hard_limit

        async with aiohttp.ClientSession() as sess:
            await sess.post(
                self.api_endpoint + "/api/v1",
                headers=self._req_header,
                data=json.dumps(body),
                ssl=self.ssl_context,
            )

    @error_handler
    async def remove_quota(self, fs_uid: str, inode_id: int) -> None:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            await self._build_request(
                sess,
                "DELETE",
                f"/fileSystems/{fs_uid}/quota/{inode_id}",
            )

    @error_handler
    async def check_health(self) -> str:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, "GET", "/healthcheck")
            return await response.text()

    @error_handler
    async def get_cluster_info(self) -> Mapping[str, Any]:
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(sess, "GET", "/cluster")
            data = await response.json()
            return data["data"]

    @error_handler
    async def get_metric(
        self,
        metrics: Iterable[str],
        start_time: datetime,
        end_time: Optional[datetime] = None,
        category: Optional[str] = None,
    ) -> Mapping[str, Any]:
        params = [("start_time", start_time.isoformat() + "Z")]
        if end_time is not None:
            params.append(("end_time", end_time.isoformat() + "Z"))
        if category is not None:
            params.append(("category", category))
        for metric in metrics:
            params.append(("stat", metric))
        querystring = urllib.parse.urlencode(params)
        async with aiohttp.ClientSession(
            base_url=self.api_endpoint,
        ) as sess:
            response = await self._build_request(
                sess,
                "GET",
                f"/stats?{querystring}",
            )
            data = await response.json()
            return data["data"]["all"]

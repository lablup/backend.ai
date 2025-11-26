from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Mapping, Optional

import aiohttp
from yarl import URL

from .exceptions import UnauthorizedPurityClient


class PurityClient:
    endpoint: URL
    api_token: str
    api_version: str
    _auth_token: Optional[str]

    _session: aiohttp.ClientSession

    def __init__(
        self,
        endpoint: str,
        api_token: str,
        *,
        api_version: str = "1.8",
    ) -> None:
        self.endpoint = URL(endpoint)
        self.api_token = api_token
        self.api_version = api_version
        self._auth_token = None
        self._lock = asyncio.Lock()
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> PurityClient:
        await self._lock.acquire()
        try:
            async with self._session.post(
                self.endpoint / "api" / "login",
                headers={"api-token": self.api_token},
                ssl=False,
                raise_for_status=True,
            ) as resp:
                auth_token = resp.headers["x-auth-token"]
                self._auth_token = auth_token
                _ = await resp.json()
            return self
        except Exception:
            self._auth_token = None
            self._lock.release()
            raise

    async def __aexit__(self, *exc_info) -> None:
        self._auth_token = None
        self._lock.release()

    # For the concrete API reference, check out:
    # https://purity-fb.readthedocs.io/en/latest/

    async def get_metadata(self) -> Mapping[str, Any]:
        if self._auth_token is None:
            raise UnauthorizedPurityClient("The auth token for Purity API is not initialized.")
        items = []
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "arrays"),
                headers={"x-auth-token": self._auth_token},
                params={
                    "items_returned": 10,
                    "token": pagination_token,
                },
                ssl=False,
                raise_for_status=True,
            ) as resp:
                data = await resp.json()
                for item in data["items"]:
                    items.append(item)
                pagination_token = data["pagination_info"]["continuation_token"]
                if pagination_token is None:
                    break
        if not items:
            return {}
        first = items[0]
        return {
            "id": first["id"],
            "name": first["name"],
            "os": first["os"],
            "revision": first["revision"],
            "version": first["version"],
            "blade_count": str(len(items)),
            "console_url": str(self.endpoint),
        }

    async def get_nfs_metric(
        self,
        fs_name: str,
    ) -> AsyncGenerator[Mapping[str, Any], None]:
        if self._auth_token is None:
            raise UnauthorizedPurityClient("The auth token for Purity API is not initialized.")
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "file-systems" / "performance"),
                headers={"x-auth-token": self._auth_token},
                params={
                    "names": fs_name,
                    "protocol": "NFS",
                    "items_returned": 10,
                    "token": pagination_token,
                },
                ssl=False,
                raise_for_status=True,
            ) as resp:
                data = await resp.json()
                for item in data["items"]:
                    yield item
                pagination_token = data["pagination_info"]["continuation_token"]
                if pagination_token is None:
                    break

    async def get_usage(self, fs_name: str) -> Mapping[str, Any]:
        if self._auth_token is None:
            raise UnauthorizedPurityClient("The auth token for Purity API is not initialized.")
        items = []
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "file-systems"),
                headers={"x-auth-token": self._auth_token},
                params={
                    "names": fs_name,
                    "items_returned": 10,
                    "token": pagination_token,
                },
                ssl=False,
                raise_for_status=True,
            ) as resp:
                data = await resp.json()
                for item in data["items"]:
                    items.append(item)
                pagination_token = data["pagination_info"]["continuation_token"]
                if pagination_token is None:
                    break
        if not items:
            return {}
        first = items[0]
        return {
            "capacity_bytes": data["total"]["provisioned"],
            "used_bytes": first["space"]["total_physical"],
        }

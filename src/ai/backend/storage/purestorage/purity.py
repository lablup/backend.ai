from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any, AsyncGenerator, Mapping

import aiohttp
from yarl import URL


class PurityClient:
    endpoint: URL
    api_token: str
    api_version: str
    auth_token: ContextVar[str]

    _session: aiohttp.ClientSession
    _auth_token_cvtoken: Token

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
        self.auth_token = ContextVar("auth_token")
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> PurityClient:
        async with self._session.post(
            self.endpoint / "api" / "login",
            headers={"api-token": self.api_token},
            ssl=False,
            raise_for_status=True,
        ) as resp:
            auth_token = resp.headers["x-auth-token"]
            self._auth_token_cvtoken = self.auth_token.set(auth_token)
            _ = await resp.json()
        return self

    async def __aexit__(self, *exc_info) -> None:
        self.auth_token.reset(self._auth_token_cvtoken)

    # For the concrete API reference, check out:
    # https://purity-fb.readthedocs.io/en/latest/

    async def get_metadata(self) -> Mapping[str, Any]:
        if self.auth_token is None:
            raise RuntimeError("The auth token for Purity API is not initialized.")
        items = []
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "arrays"),
                headers={"x-auth-token": self.auth_token.get()},
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
        if self.auth_token is None:
            raise RuntimeError("The auth token for Purity API is not initialized.")
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "file-systems" / "performance"),
                headers={"x-auth-token": self.auth_token.get()},
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
        if self.auth_token is None:
            raise RuntimeError("The auth token for Purity API is not initialized.")
        items = []
        pagination_token = ""
        while True:
            async with self._session.get(
                (self.endpoint / "api" / self.api_version / "file-systems"),
                headers={"x-auth-token": self.auth_token.get()},
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

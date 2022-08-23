from __future__ import annotations

from typing import Any, Mapping

import aiohttp


class QuotaManager:

    endpoint: str
    user: str
    password: str
    api_version: str
    _session: aiohttp.ClientSession
    # volume_name: str

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
        *,
        api_version: str = "12",
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.api_version = api_version
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def list_all_quota(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/quota/quotas",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["quotas"]

    async def get_quota_by_quota_id(self, quota_id) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/quota/quotas/{quota_id}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=False,
        ) as resp:
            data = await resp.json()
        return data["quotas"][0]

    async def get_quota_by_path(self, path) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/quota/quotas/{path}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=False,
        ) as resp:
            data = await resp.json()
        return data["quotas"][0]

    async def create_quota(
        self,
        path: str,
        type: str,
        include_snapshots: bool = False,
        persona: str | None = None,
        thresholds: object = {},
        ignore_limit_checks: bool = False,
        force: bool = False,  # Force creation of quotas on the root of /ifs or percent based quotas.
        container: bool = False,
        thresholds_on: str = "fslogicalsize",
        enforced: bool = False,  # True if the quota provides enforcement, otherwise an accounting quota.
    ) -> Mapping[str, Any]:
        dataobj = {
            "include_snapshots": include_snapshots,
            "path": path,
            "type": type,
            "persona": persona,
            "force": force,
            "ignore_limit_checks": ignore_limit_checks,
            "thresholds": thresholds,
            "container": container,
            "thresholds_on": thresholds_on,
            "enforced": enforced,
        }
        headers = {"content-type": "application/json", "accept": "application/hal+json"}
        async with self._session.post(
            f"{self.endpoint}/platform/{self.api_version}/quota/quotas",
            auth=aiohttp.BasicAuth(self.user, self.password),
            headers=headers,
            data=dataobj,
            ssl=False,
            raise_for_status=True,
        ) as resp:
            msg = await resp.json()
        return msg

    async def delete_quota(self, quota_id):
        async with self._session.delete(
            f"{self.endpoint}/platform/{self.api_version}/quota/quotas/{quota_id}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            msg = await resp.json()
        return msg

    async def update_quota(self):
        pass

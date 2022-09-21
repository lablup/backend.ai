from __future__ import annotations

from typing import Any, Mapping

import aiohttp
from aiohttp.client_reqrep import ClientResponse


class QuotaManager:

    endpoint: str
    user: str
    password: str
    _session: aiohttp.ClientSession
    svm: str
    volume_name: str

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
        svm: str,
        volume_name: str,
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self._session = aiohttp.ClientSession()
        self.svm = svm
        self.volume_name = volume_name

    async def aclose(self) -> None:
        await self._session.close()

    async def list_quotarules(self):
        async with self._session.get(
            f"{self.endpoint}/api/storage/quota/rules",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=False,
        ) as resp:
            data = await resp.json()
            await self._session.close()

        rules = [rule for rule in data["uuid"]]
        self.rules = rules
        return rules

    async def list_all_qtrees_with_quotas(self) -> Mapping[str, Any]:
        rules = await self.list_quotarules()
        qtrees = {}

        for rule in rules:
            async with self._session.get(
                f"{self.endpoint}/api/storage/quota/rules/{rule}",
                auth=aiohttp.BasicAuth(self.user, self.password),
                ssl=False,
                raise_for_status=False,
            ) as resp:
                data = await resp.json()
                qtree_uuid = data["uuid"]
                qtree_name = data["qtree"]["name"]
                qtrees[qtree_uuid] = qtree_name
        self.qtrees = qtrees
        return qtrees

    async def get_quota_by_rule(self, rule_uuid) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/quota/rules/{rule_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=False,
        ) as resp:
            data = await resp.json()
            quota = {}
            if data.get("space"):
                quota["space"] = data["space"]
            if data.get("files"):
                quota["files"] = data["files"]
        return quota

    async def get_quota_by_qtree_name(self, qtree_name) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/quota/rules?volume={self.volume_name}&qtree={qtree_name}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=False,
        ) as resp:
            data = await resp.json()
            rule_uuid = data["records"][0]["uuid"]
            quota = await self.get_quota_by_rule(rule_uuid)
        return quota

    # For now, Only Read / Update operation for qtree is available
    # in NetApp ONTAP Plugin of Backend.AI
    async def create_quotarule_qtree(
        self,
        qtree_name: str,
        spahali: int,
        spasoli: int,
        fihali: int,
        fisoli: int,
    ) -> Mapping[str, Any]:
        dataobj = {
            "svm": {"name": self.svm},
            "volume": {"name": self.volume_name},
            "type": "tree",
            "space": {"hard_limit": spahali, "soft_limit": spasoli},
            "files": {"hard_limit": fihali, "soft_limit": fisoli},
            "qtree": {"name": qtree_name},
        }

        headers = {"content-type": "application/json", "accept": "application/hal+json"}

        async with self._session.post(
            f"{self.endpoint}/api/storage/quota/rules",
            auth=aiohttp.BasicAuth(self.user, self.password),
            headers=headers,
            json=dataobj,
            ssl=False,
            raise_for_status=True,
        ) as resp:

            msg = await resp.json()
        return msg

    async def update_quotarule_qtree(
        self,
        spahali: int,
        spasoli: int,
        fihali: int,
        fisoli: int,
        rule_uuid,
    ) -> ClientResponse:
        dataobj = {
            "space": {"hard_limit": spahali, "soft_limit": spasoli},
            "files": {"hard_limit": fihali, "soft_limit": fisoli},
        }

        headers = {"content-type": "application/json", "accept": "application/hal+json"}

        async with self._session.patch(
            f"{self.endpoint}/api/storage/quota/rules/{rule_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            headers=headers,
            json=dataobj,
            ssl=False,
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    # For now, Only Read / Update operation for qtree is available
    # in NetApp ONTAP Plugin of Backend.AI
    async def delete_quotarule_qtree(self, rule_uuid) -> ClientResponse:
        headers = {"content-type": "application/json", "accept": "application/hal+json"}

        async with self._session.delete(
            f"{self.endpoint}/api/storage/quota/rules/{rule_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            headers=headers,
            ssl=False,
            raise_for_status=True,
        ) as resp:
            return await resp.json()

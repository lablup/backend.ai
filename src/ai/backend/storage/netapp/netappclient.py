from __future__ import annotations

import json
from typing import Any, List, Mapping

import aiohttp


class NetAppClient:

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
        self.svm = svm
        self.volume_name = volume_name
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def get_metadata(self) -> Mapping[str, Any]:
        volume_uuid = await self.get_volume_uuid_by_name()
        data = await self.get_volume_info(volume_uuid)
        qos = await self.get_qos_by_volume_id(volume_uuid)
        qos_policies = await self.get_qos_policies()
        qtree_metadata = await self.get_default_qtree_by_volume_id(volume_uuid)
        qtree = await self.get_qtree_info(qtree_metadata.get("id"))

        # mapping certain data for better explanation
        volume_qtree_cluster = {
            # ------ use volume info ------
            "id": data["uuid"],
            "local_tier": data["aggregates"][0]["name"],
            "create_time": data["create_time"],
            "snapshot_policy": data["snapshot_policy"]["name"],
            "snapmirroring": str(data["snapmirror"]["is_protected"]),
            "state": data["state"],
            "style": data["style"],
            "svm_name": data["svm"]["name"],
            "svm_id": data["svm"]["uuid"],
            # ------ use qtree info ------
            "name": qtree["name"],
            "path": qtree["path"],
            "security_style": qtree["security_style"],
            "export_policy": qtree["export_policy"]["name"],
            "timestamp": qtree["statistics"].get("timestamp"),  # last check time
        }
        # optional values to add in volume_qtree_cluster
        if qos:
            volume_qtree_cluster.update({"qos": json.dumps(qos["policy"])})
        if qos_policies:
            volume_qtree_cluster.update({"qos_policies": json.dumps(qos_policies)})
        return volume_qtree_cluster

    async def get_usage(self) -> Mapping[str, Any]:
        # volume specific usage check
        uuid = await self.get_volume_uuid_by_name()
        data = await self.get_volume_info(uuid)
        return {
            "capacity_bytes": data["space"]["available"],
            "used_bytes": data["space"]["used"],
        }

    async def get_list_volumes(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["records"]

    async def get_volume_name_by_uuid(self, volume_uuid) -> str:
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes?uuid={volume_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            name = data["records"][0]["name"]
        return name

    async def get_volume_uuid_by_name(self) -> str:
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes?name={self.volume_name}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            uuid = data["records"][0]["uuid"]
            return uuid

    async def get_volume_info(self, volume_uuid) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes/{volume_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data

    async def get_default_qtree_by_volume_id(self, volume_uuid) -> Mapping[str, Any]:
        qtrees = await self.list_qtrees_by_volume_id(volume_uuid)
        for qtree in qtrees:
            # skip the default qtree made by NetApp ONTAP internally
            # It will not be used in Backend.AI NetApp ONTAP Plugin
            if not qtree["name"]:
                continue
            else:
                return qtree
        return {}

    async def get_qtree_name_by_id(self, qtree_id) -> str:
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees?id={qtree_id}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["name"]

    async def get_qtree_id_by_name(self, qtree_name) -> str:
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees?name={qtree_name}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            id = str(data["records"][0]["id"]) if data["num_records"] > 0 else ""
        return id

    async def list_qtrees_by_volume_id(self, volume_uuid) -> List[Mapping[str, Any]]:
        if not volume_uuid:
            volume_uuid = await self.get_volume_uuid_by_name()
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees/{volume_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["records"]

    async def get_qtree_info(self, qtree_id) -> Mapping[str, Any]:
        uuid = await self.get_volume_uuid_by_name()
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees/{uuid}/{qtree_id}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data

    async def get_qos_policies(self) -> List[Mapping[str, Any]]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/qos/policies",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            qos_policies_metadata = data["records"]
            qos_policies = []
            for qos in qos_policies_metadata:
                policy = await self.get_qos_by_uuid(qos["uuid"])
                qos_policies.append(policy)
        return qos_policies

    async def get_qos_by_uuid(self, qos_uuid) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/qos/policies/{qos_uuid}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            fixed = data["fixed"]
            qos_policy = {
                "uuid": data["uuid"],
                "name": data["name"],
                "fixed": {
                    "max_throughput_iops": fixed.get("max_throughput_iops", 0),
                    "max_throughput_mbps": fixed.get("max_throughput_mbps", 0),
                    "min_throughput_iops": fixed.get("min_throughput_iops", 0),
                    "min_throughput_mbps": fixed.get("min_throughput_mbps", 0),
                    "capacity_shared": fixed["capacity_shared"],
                },
                "svm": data["svm"],
            }
            return qos_policy

    async def get_qos_by_volume_id(self, volume_uuid) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes/{volume_uuid}?fields=qos",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["qos"]

from __future__ import annotations

import json
from typing import Any, List, Mapping

import aiohttp

# from manager.src.ai.backend.manager.api import auth


class DellEMCClient:
    endpoint: str
    user: str
    password: str
    api_version: str
    system_name: str
    _session: aiohttp.ClientSession

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
        *,
        api_version: str = "12",
        system_name: str = "nfs",
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.api_version = api_version
        self.system_name = system_name
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def get_metadata(self) -> Mapping[str, Any]:
        cluster_metadata = await self.get_cluster_metadata()
        node_metadata = await self.get_node_metadata()
        volume_cluster = {
            "cluster": json.dumps(cluster_metadata),
            "nodes": json.dumps(node_metadata),
        }
        return volume_cluster

    async def get_usage(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/storagepool/storagepools",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return {
            "capacity_bytes": data["storagepools"][0]["usage"]["total_bytes"],
            "used_bytes": data["storagepools"][0]["usage"]["used_bytes"],
        }

    async def get_list_lnn(self) -> List[int]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/storagepool/storagepools",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["storagepools"][0]["lnns"]

    async def get_node_hardware_info_by_lnn(self, lnn) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/cluster/nodes/{lnn}/hardware",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            node = data["nodes"][0]
        return {
            "id": node["id"],
            "model": node["product"],
            "configuration": node["configuration_id"],
            "serial_number": node["serial_number"],
        }

    async def get_node_status_by_lnn(self, lnn) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/cluster/nodes/{lnn}/status/nvram",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            node = data["nodes"][0]
        return {
            "batteries": node["batteries"],
            # "capacity": node["capacity"],
        }

    async def get_cluster_metadata(self) -> List[Mapping[str, Any]]:
        try:
            cluster_metadata = []
            cluster_metadata.append(
                {
                    "config": await self.get_cluster_config(),
                    "interface": await self.get_cluster_interface(),
                }
            )
            return cluster_metadata
        except Exception as e:
            raise (e)

    async def get_cluster_config(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/cluster/config",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return {
            "name": data["name"],
            "release": data["onefs_version"]["release"],
            "build": data["onefs_version"]["build"],
            "local_lnn": data["local_lnn"],
        }

    async def get_cluster_interface(self) -> List[Mapping[str, Any]]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/network/interfaces",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["interfaces"]

    async def get_node_metadata(self) -> List[Mapping[str, Any]]:
        try:
            lnns = await self.get_list_lnn()
            node_metadata = []
            for lnn in lnns:
                node_metadata.append(
                    {
                        "hardware": await self.get_node_hardware_info_by_lnn(lnn),
                        "status": await self.get_node_status_by_lnn(lnn),
                    }
                )
            return node_metadata
        except Exception as e:
            raise (e)

    async def get_drive_stats(self) -> Mapping[int, any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/statistics/summary/drive",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["drive"]

    async def get_protocol_stats(self) -> Mapping[str, any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/statistics/summary/protocol-stats",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["protocol-stats"]

    async def get_workload_stats(self) -> Mapping[str, any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/statistics/summary/workload?system_names={self.system_name}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            return data["workload"][0]

    async def get_system_stats(self) -> Mapping[int, any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/statistics/summary/system",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["system"][0]


"""
    async def get_workload_stats(self) -> Mapping[int, any]:
        async with self._session.get(
            f"{self.endpoint}/platform/{self.api_version}/statistics/summary/workload",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["workload"]
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping

import aiohttp

# from manager.src.ai.backend.manager.api import auth


class DellEMCClient:
    endpoint: str
    user: str
    password: str
    _session: aiohttp.ClientSession
    # svm: str
    # volume_name: str

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    """
    async def get_metadata(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/cluster/config",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        volume_cluster = {
            "description": data["description"],
            "encoding": data["encoding"],
            "guid": data["guid"],
            "has_quorum": str(data["has_quorum"]),
            "is_compliance": str(data["is_compliance"]),
            "is_virtual": str(data["is_virtual"]),
            "is_vonefs": str(data["is_vonefs"]),
            "join_mode": data["join_mode"],
            "local_devid": str(data["local_devid"]),
            "local_lnn": str(data["local_lnn"]),
            "local_serial": data["local_serial"],
            "name": data["name"],
            "devices": json.dumps(data["devices"]),
            "onefs_version": json.dumps(data["onefs_version"]),
            "timezone": str(data["timezone"]),
            "upgrade_type": str(data["upgrade_type"]),
        }
        return volume_cluster
    """

    async def get_metadata(self) -> Mapping[str, Any]:
        # TODO: request-timeout-error
        node_metadata = await self.get_node_metadata()

        volume_cluster = {"nodes": json.dumps(node_metadata)}
        return volume_cluster

    async def get_usage(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/storagepool/storagepools",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return {
            "capacity_bytes": data["storagepools"][0]["usage"]["avail_bytes"],
            "used_bytes": data["storagepools"][0]["usage"]["used_bytes"],
        }

    # device info such as devid, guid, is_up, lnn
    async def get_list_devices(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/cluster/config",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["devices"]

    async def get_list_lnn(self) -> List[int]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/storagepool/storagepools",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["storagepools"][0]["lnns"]

    async def get_node_hardware_info_by_lnn(self, lnn) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/cluster/nodes/{lnn}/hardware",
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
            f"{self.endpoint}/platform/12/cluster/nodes/{lnn}/status",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            node = data["nodes"][0]
        return {
            "capacity": node["capacity"],
            "batteries": node["nvram"]["batteries"],
        }

    async def get_node_metadata(self) -> List[Dict[str, Mapping[str, Any]]]:
        lnns = await self.get_list_lnn()
        node_metadata = {}
        for lnn in lnns:
            node_metadata[lnn] = {
                "hardware": await self.get_node_hardware_info_by_lnn(lnn),
                "status": await self.get_node_status_by_lnn(lnn),
            }
        return node_metadata

    # for performance metric
    async def get_protocol_stats(self) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/statistics/summary/protocol-stats",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["protocol-stats"]

    # nodes=<string> A comma separated list. Specify node(s) for which statistics should be reported
    async def get_protocol_stats_by_node(self, nodes) -> Mapping[str, Any]:
        async with self._session.get(
            f"{self.endpoint}/platform/12/statistics/summary/protocol-stats?nodes={nodes}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
        return data["protocol-stats"]

from __future__ import annotations

import enum
import json
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Mapping

import aiohttp


class QuotaTypes(enum.StrEnum):
    DIRECTORY = "directory"
    USER = "user"
    GROUP = "group"


@dataclass
class QuotaThresholds:
    hard: int
    soft: int


class OneFSClient:
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
        self._request_opts = {
            "auth": aiohttp.BasicAuth(self.user, self.password),
            "ssl": False,
            "raise_for_status": True,
        }

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

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        async with self._session.request(
            method,
            f"{self.endpoint}/platform/{self.api_version}/{path}",
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
            **kwargs,
        ) as resp:
            yield resp

    async def get_usage(self) -> Mapping[str, Any]:
        async with self._request("GET", "storagepool/storagepools") as resp:
            data = await resp.json()
        return {
            "capacity_bytes": data["storagepools"][0]["usage"]["total_bytes"],
            "used_bytes": data["storagepools"][0]["usage"]["used_bytes"],
        }

    async def get_list_lnn(self) -> List[int]:
        async with self._request("GET", "storagepool/storagepools") as resp:
            data = await resp.json()
        return data["storagepools"][0]["lnns"]

    async def get_node_hardware_info_by_lnn(self, lnn) -> Mapping[str, Any]:
        async with self._request("GET", f"cluster/nodes/{lnn}/hardware") as resp:
            data = await resp.json()
            node = data["nodes"][0]
        return {
            "id": node["id"],
            "model": node["product"],
            "configuration": node["configuration_id"],
            "serial_number": node["serial_number"],
        }

    async def get_node_status_by_lnn(self, lnn) -> Mapping[str, Any]:
        async with self._request("GET", f"cluster/nodes/{lnn}/status/nvram") as resp:
            data = await resp.json()
            node = data["nodes"][0]
        return {
            "batteries": node["batteries"],
            # "capacity": node["capacity"],
        }

    async def get_cluster_metadata(self) -> List[Dict[str, Any]]:
        try:
            cluster_metadata = []
            cluster_metadata.append({
                "config": await self.get_cluster_config(),
                "interface": await self.get_cluster_interface(),
            })
            return cluster_metadata
        except Exception as e:
            raise (e)

    async def get_cluster_config(self) -> Mapping[str, Any]:
        async with self._request("GET", "cluster/config") as resp:
            data = await resp.json()
        return {
            "name": data["name"],
            "release": data["onefs_version"]["release"],
            "build": data["onefs_version"]["build"],
            "local_lnn": data["local_lnn"],
        }

    async def get_cluster_interface(self) -> List[Mapping[str, Any]]:
        async with self._request("GET", "network/interfaces") as resp:
            data = await resp.json()
        return data["interfaces"]

    async def get_node_metadata(self) -> List[Dict[str, Mapping[str, Any]]]:
        try:
            lnns = await self.get_list_lnn()
            node_metadata = []
            for lnn in lnns:
                node_metadata.append({
                    "hardware": await self.get_node_hardware_info_by_lnn(lnn),
                    "status": await self.get_node_status_by_lnn(lnn),
                })
            return node_metadata
        except Exception as e:
            raise (e)

    async def get_drive_stats(self) -> Mapping[int, Any]:
        async with self._request("GET", "statistics/summary/drive") as resp:
            data = await resp.json()
        return data["drive"]

    async def get_protocol_stats(self) -> Mapping[str, Any]:
        async with self._request("GET", "statistics/summary/protocol-stats") as resp:
            data = await resp.json()
        return data["protocol-stats"]

    async def get_workload_stats(self) -> Mapping[str, Any]:
        async with self._request(
            "GET",
            "statistics/summary/workload",
            params={"system_names": self.system_name},
        ) as resp:
            data = await resp.json()
            return data["workload"][0]

    async def get_system_stats(self) -> Mapping[int, Any]:
        async with self._request("GET", "statistics/summary/system") as resp:
            data = await resp.json()
        return data["system"][0]

    async def list_all_quota(self) -> Mapping[str, Any]:
        async with self._request("GET", "quota/quotas") as resp:
            data = await resp.json()
        return data["quotas"]

    async def get_quota(self, quota_id: str) -> Mapping[str, Any]:
        async with self._request("GET", f"quota/quotas/{quota_id}") as resp:
            data = await resp.json()
        return data["quotas"][0]

    async def create_quota(
        self,
        path: os.PathLike,
        type_: QuotaTypes,
        thresholds: QuotaThresholds,
    ) -> Mapping[str, Any]:
        data = {
            "path": os.fsdecode(path),
            "type": type_.value,
            "include_snapshots": False,
            "thresholds": thresholds,
            "thresholds_on": "fslogicalsize",
            "enforced": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/hal+json",
        }
        async with self._request(
            "POST",
            "quota/quotas",
            headers=headers,
            data=data,
        ) as resp:
            msg = await resp.json()
        return msg

    async def delete_quota(self, quota_id):
        async with self._request(
            "DELETE",
            f"quota/quotas/{quota_id}",
        ) as resp:
            msg = await resp.json()
        return msg

    async def update_quota(self, quota_id: str, thresholds: QuotaThresholds):
        data = {
            "thresholds": thresholds,
        }
        async with self._request(
            "PUT",
            f"quota/quotas/{quota_id}",
            data=data,
        ) as resp:
            msg = await resp.json()
        return msg

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import aiohttp

from ai.backend.common.dto.clients.storage_backends.dellemc.request import (
    OneFSCreateQuotaRequest,
    OneFSUpdateQuotaRequest,
    OneFSWorkloadStatsQuery,
)
from ai.backend.common.dto.clients.storage_backends.dellemc.response import (
    OneFSClusterConfig,
    OneFSClusterMetadata,
    OneFSCreatedQuota,
    OneFSDriveStats,
    OneFSMetadata,
    OneFSNetworkInterface,
    OneFSNodeHardware,
    OneFSNodeLnns,
    OneFSNodeMetadata,
    OneFSNodeStatus,
    OneFSProtocolStats,
    OneFSQuota,
    OneFSSystemStats,
    OneFSUsage,
    OneFSWorkloadStats,
)
from ai.backend.common.dto.clients.storage_backends.dellemc.types import (
    OneFSQuotaID,
)
from ai.backend.common.json import dump_json_str


@dataclass
class OneFSClientArgs:
    endpoint: str
    user: str
    password: str
    api_version: str = "12"
    system_name: str | None = "nfs"


class OneFSClient:
    """Dell EMC PowerScale OneFS platform API client using HTTP basic auth."""

    _endpoint: str
    _user: str
    _password: str
    _api_version: str
    _system_name: str | None
    _session: aiohttp.ClientSession

    def __init__(self, args: OneFSClientArgs) -> None:
        self._endpoint = args.endpoint
        self._user = args.user
        self._password = args.password
        self._api_version = args.api_version
        self._system_name = args.system_name
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        async with self._session.request(
            method,
            f"{self._endpoint}/platform/{self._api_version}/{path}",
            auth=aiohttp.BasicAuth(self._user, self._password),
            ssl=False,
            raise_for_status=True,
            **kwargs,
        ) as resp:
            yield resp

    async def get_metadata(self) -> OneFSMetadata:
        cluster_metadata = await self.get_cluster_metadata()
        node_metadata = await self.get_node_metadata()
        return OneFSMetadata(
            cluster=dump_json_str([item.model_dump(mode="json") for item in cluster_metadata]),
            nodes=dump_json_str([item.model_dump(mode="json") for item in node_metadata]),
        )

    async def get_usage(self) -> OneFSUsage:
        async with self._request("GET", "storagepool/storagepools") as resp:
            data = await resp.json()
        return OneFSUsage(
            capacity_bytes=int(data["storagepools"][0]["usage"]["total_bytes"]),
            used_bytes=int(data["storagepools"][0]["usage"]["used_bytes"]),
        )

    async def get_list_lnn(self) -> OneFSNodeLnns:
        async with self._request("GET", "storagepool/storagepools") as resp:
            data = await resp.json()
        return OneFSNodeLnns(lnns=[int(lnn) for lnn in data["storagepools"][0]["lnns"]])

    async def get_node_hardware_info_by_lnn(self, lnn: int) -> OneFSNodeHardware:
        async with self._request("GET", f"cluster/nodes/{lnn}/hardware") as resp:
            data = await resp.json()
        node = data["nodes"][0]
        return OneFSNodeHardware(
            id=node["id"],
            model=node["product"],
            configuration=node["configuration_id"],
            serial_number=node["serial_number"],
        )

    async def get_node_status_by_lnn(self, lnn: int) -> OneFSNodeStatus:
        async with self._request("GET", f"cluster/nodes/{lnn}/status/nvram") as resp:
            data = await resp.json()
        node = data["nodes"][0]
        return OneFSNodeStatus(batteries=node["batteries"])

    async def get_cluster_metadata(self) -> list[OneFSClusterMetadata]:
        return [
            OneFSClusterMetadata(
                config=await self.get_cluster_config(),
                interface=await self.get_cluster_interface(),
            )
        ]

    async def get_cluster_config(self) -> OneFSClusterConfig:
        async with self._request("GET", "cluster/config") as resp:
            data = await resp.json()
        return OneFSClusterConfig(
            name=data["name"],
            release=data["onefs_version"]["release"],
            build=data["onefs_version"]["build"],
            local_lnn=data["local_lnn"],
        )

    async def get_cluster_interface(self) -> list[OneFSNetworkInterface]:
        async with self._request("GET", "network/interfaces") as resp:
            data = await resp.json()
        return [OneFSNetworkInterface.model_validate(item) for item in data["interfaces"]]

    async def get_node_metadata(self) -> list[OneFSNodeMetadata]:
        lnns = (await self.get_list_lnn()).lnns
        return [
            OneFSNodeMetadata(
                hardware=await self.get_node_hardware_info_by_lnn(lnn),
                status=await self.get_node_status_by_lnn(lnn),
            )
            for lnn in lnns
        ]

    async def get_drive_stats(self) -> list[OneFSDriveStats]:
        async with self._request("GET", "statistics/summary/drive") as resp:
            data = await resp.json()
        return [OneFSDriveStats.model_validate(item) for item in data["drive"]]

    async def get_protocol_stats(self) -> OneFSProtocolStats:
        async with self._request("GET", "statistics/summary/protocol-stats") as resp:
            data = await resp.json()
        return OneFSProtocolStats.model_validate(data["protocol-stats"])

    async def get_workload_stats(self) -> OneFSWorkloadStats | None:
        query = OneFSWorkloadStatsQuery(system_names=self._system_name)
        async with self._request(
            "GET",
            "statistics/summary/workload",
            params=query.model_dump(mode="json", by_alias=True, exclude_none=True),
        ) as resp:
            data = await resp.json()
        if not data["workload"]:
            return None
        return OneFSWorkloadStats.model_validate(data["workload"][0])

    async def get_system_stats(self) -> OneFSSystemStats | None:
        async with self._request("GET", "statistics/summary/system") as resp:
            data = await resp.json()
        if not data["system"]:
            return None
        return OneFSSystemStats.model_validate(data["system"][0])

    async def list_all_quota(self) -> list[OneFSQuota]:
        async with self._request("GET", "quota/quotas") as resp:
            data = await resp.json()
        return [OneFSQuota.model_validate(item) for item in data["quotas"]]

    async def get_quota(self, quota_id: OneFSQuotaID) -> OneFSQuota:
        async with self._request("GET", f"quota/quotas/{quota_id}") as resp:
            data = await resp.json()
        return OneFSQuota.model_validate(data["quotas"][0])

    async def create_quota(self, request: OneFSCreateQuotaRequest) -> OneFSCreatedQuota:
        async with self._request(
            "POST",
            "quota/quotas",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        ) as resp:
            return OneFSCreatedQuota.model_validate(await resp.json())

    async def delete_quota(self, quota_id: OneFSQuotaID) -> None:
        async with self._request(
            "DELETE",
            f"quota/quotas/{quota_id}",
        ) as _:
            return

    async def update_quota(self, quota_id: OneFSQuotaID, request: OneFSUpdateQuotaRequest) -> None:
        async with self._request(
            "PUT",
            f"quota/quotas/{quota_id}",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        ) as _:
            return

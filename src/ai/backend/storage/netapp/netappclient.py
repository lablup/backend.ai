from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import (
    Any,
    List,
    Mapping,
    NotRequired,
    Optional,
    Sequence,
    TypeAlias,
    TypedDict,
)

import aiohttp


VolumeID: TypeAlias = uuid.UUID
QTreeID: TypeAlias = int


class SpaceInfo(TypedDict):
    available: int
    used: int
    size: int


class VolumeInfo(TypedDict):
    name: str
    uuid: VolumeID
    path: Path
    space: NotRequired[SpaceInfo]
    statistics: NotRequired[dict[str, Any]]


class QTreeInfo(TypedDict):
    id: int
    name: str
    path: Path
    security_style: NotRequired[str]
    export_policy: NotRequired[dict[str, Any]]
    statistics: NotRequired[dict[str, Any]]


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
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    async def get_volume_metadata(self, volume_id: VolumeID) -> Mapping[str, Any]:
        raise NotImplementedError
        # qos = await self.get_qos_by_volume_id(volume_id)
        # qos_policies = await self.get_qos_policies()
        # qtree = await self.get_default_qtree(
        #     volume_id,
        #     [
        #         "security_style",
        #         "export_policy",
        #         "statistics",
        #     ],
        # )

        # # mapping certain data for better explanation
        # volume_qtree_cluster = {
        #     # ------ use volume info ------
        #     "id": data["uuid"],
        #     "local_tier": data["aggregates"][0]["name"],
        #     "create_time": data["create_time"],
        #     "snapshot_policy": data["snapshot_policy"]["name"],
        #     "snapmirroring": str(data["snapmirror"]["is_protected"]),
        #     "state": data["state"],
        #     "style": data["style"],
        #     "svm_name": data["svm"]["name"],
        #     "svm_id": data["svm"]["uuid"],
        #     # ------ use qtree info ------
        #     "name": qtree["name"],
        #     "path": qtree["path"],
        #     "security_style": qtree["security_style"],
        #     "export_policy": qtree["export_policy"]["name"],
        #     "timestamp": qtree["statistics"].get("timestamp"),  # last check time
        # }
        # # optional values to add in volume_qtree_cluster
        # if qos:
        #     volume_qtree_cluster.update({"qos": json.dumps(qos["policy"])})
        # if qos_policies:
        #     volume_qtree_cluster.update({"qos_policies": json.dumps(qos_policies)})
        # return volume_qtree_cluster

    async def list_volumes(
        self, extra_fields: Optional[Sequence[str]] = None
    ) -> Mapping[VolumeID, VolumeInfo]:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes",
            params={"fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            return {
                VolumeID(record["uuid"]): {
                    "uuid": VolumeID(record["uuid"]),
                    "name": record["name"],
                    "path": Path(record["path"]),
                }
                for record in data["records"]
            }

    async def get_volume_by_name(
        self,
        name: str,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> VolumeInfo:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes",
            params={"name": name, "fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            record = data["records"][0]
            return {
                "uuid": VolumeID(record["uuid"]),
                "name": record["name"],
                "path": Path(record["path"]),
            }

    async def get_volume_by_id(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> VolumeInfo:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes/{volume_id}",
            params={"fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            record = await resp.json()
            return {
                "uuid": VolumeID(record["uuid"]),
                "name": record["name"],
                "path": Path(record["path"]),
            }

    async def get_volume_metric_by_id(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> dict[str, Any]:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/volumes/{volume_id}/metrics",
            params={"fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    async def list_qtrees(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> Sequence[QTreeInfo]:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees/{volume_id}",
            params={"fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            return [
                {
                    "name": record["name"],
                    "id": int(record["id"]),
                    "path": Path(record["path"]),
                }
                for record in data["records"]
            ]

    async def get_default_qtree(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> QTreeInfo:
        return await self.get_qtree_by_id(volume_id, 0, extra_fields=extra_fields)

    async def get_qtree_by_id(
        self,
        volume_id: VolumeID,
        qtree_id: QTreeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> QTreeInfo:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees/{volume_id}/{qtree_id}",
            params={"fields": ",".join(_extra_fields)},
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            record = await resp.json()
            return {
                "name": record["name"],
                "id": int(record["id"]),
                "path": Path(record["path"]),
            }

    async def get_qtree_by_name(
        self,
        volume_id: VolumeID,
        name: str,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> QTreeInfo:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self._session.get(
            f"{self.endpoint}/api/storage/qtrees",
            params={
                "name": name,
                "volume.uuid": str(volume_id),
                "fields": ",".join(_extra_fields),
            },
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            if data["num_records"] > 0:
                record = data["records"][0]
                return {
                    "name": record["name"],
                    "id": int(record["id"]),
                    "path": Path(record["path"]),
                }
            else:
                raise RuntimeError(f"No qtree {name} found in the volume {volume_id}")

    async def create_qtree(self, svm_id: str, volume_id: VolumeID, qtree_name: str):
        async with self._session.post(
            f"{self.endpoint}/api/storage/qtrees",
            params={
                "svm": {"uuid": svm_id},
                "volume": {"uuid": str(volume_id)},
                "name": qtree_name,
            },
            auth=aiohttp.BasicAuth(self.user, self.password),
            ssl=False,
            raise_for_status=True,
        ) as resp:
            data = await resp.json()
            return data

    async def update_quota_rule(
        self,
        svm_id: str,
        volume_id: VolumeID,
        qtree_name: str,
        config: QuotaConfig,
    ):
        async with self._session.post(
            f"{self.endpoint}/api/storage/quota/rules",
            data={
                "svm": {"uuid": svm_id},
                "volume": {"uuid": str(volume_id)},
                "type": "tree",  # fix qtree-based quota
                "qtree": {"name": qtree_name},
                "space": {"hard_limit": config.hard_limit, "soft_limit": config.soft_limit},
                # 'files': {'hard_limit': file_limit, 'soft_limit': file_limit},  # not supported yet from Backend.AI
            },
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

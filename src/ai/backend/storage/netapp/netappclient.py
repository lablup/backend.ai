"""
A thin wrapper of the NetApp ONTAP API.


Generic ONTAP error codes
-------------------------

1	    An entry with the same identifiers already exists.
2	    A field has an invalid value, is missing, or an extra field was provided.
3	    The operation is not supported.
4	    An entry with the specified identifiers was not found.
6	    Permission denied.
7	    Resource limit exceeded.
8	    Resource in use.
65541	RPC timed out.
65552	Generic RPC failure.
65562	Internal RPC error
262145	Application code returned an unexpected exception.
262160	There are too many requets already being processed. Retry after a short delay.
262177	Missing value.
262179	Unexpected argument. Argument shown in error message body.
262185	Invalid value with value in the body of the error.
262186	A field is used in an invalid context with another field,
        as shown in error message body.
262188	A field was specified twice. Location of assignments shown in error message body.
262190	You must provide one or more values to apply your changes.
262196	Field cannot be set in this operation.
262197	Invalid value provided for field. Value and field shown in error message body.
262198	A request body is not allowed on GET, HEAD, and DELETE.
262199	Invalid JSON with error location provided in body of the error.
262200	Invalid JSON range, with range provided in the body of the error.
262201	Invalid JSON due to unknown formatting issue.
262202	Field is considered secret and should not be provided in the URL.
262210	Unable to retrieve all required records within the timeout.
        This "order_by" query is not supported under the current system load
        with the current number of records in the collection.
262211	POST request on a REST API does not support filtering on an attribute.
        Attributes must be in the request body.
262212	Request is missing required value.
262220	Wildcard fields=* is not allowed for CLI-based REST APIs.
262245	Invalid value with reason provided in body of the error.
262247	Invalid value for a field, with value and field in body of the error.
262248	A value is missing assignment operator.
262249	Field name is not supported for GET requests because it is not a readable attribute.
262250	Field name cannot be queried in a GET request because it is not a readable attribute.
262254	Invalid JSON input, an array was expected.
262255	An array was found in the JSON when it was not expected.
262268	The field is not supported as an order_by= field.
262277	The query_fields and query parameters may only be specified for GET requests.
262282	Property was specified twice.
262286	Mismatching braces found in the fields= query.
393271	A node is out of quorum. Body of error message identifies node.
39387137	A provided URL is invalid.
"""

from __future__ import annotations

import asyncio
import contextlib
import enum
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    List,
    Mapping,
    NotRequired,
    Optional,
    Sequence,
    TypeAlias,
    TypedDict,
)

import aiohttp

from ..exception import ExternalError
from ..types import QuotaConfig, QuotaUsage

StorageID: TypeAlias = uuid.UUID
VolumeID: TypeAlias = uuid.UUID
QTreeID: TypeAlias = int


class JobResponseCode(enum.StrEnum):
    QUOTA_ALEADY_ENABLED = "5308507"


class AsyncJobResult(TypedDict):
    state: str
    code: str | None
    message: str | None


class SpaceInfo(TypedDict):
    available: int
    used: int
    size: int


class SVMInfo(TypedDict):
    uuid: str
    name: str


class VolumeInfo(TypedDict):
    name: str
    uuid: VolumeID
    path: Path
    space: NotRequired[SpaceInfo]
    statistics: NotRequired[dict[str, Any]]
    svm: NotRequired[SVMInfo]


class QTreeInfo(TypedDict):
    id: int
    name: str
    path: Path
    security_style: NotRequired[str]
    export_policy: NotRequired[dict[str, Any]]
    statistics: NotRequired[dict[str, Any]]


class NetAppClientError(ExternalError):
    pass


class NetAppClient:
    endpoint: str
    user: str
    password: str
    user_id: int
    group_id: int
    _session: aiohttp.ClientSession

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
        user_id: int,
        group_id: int,
    ) -> None:
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.user_id = user_id
        self.group_id = group_id
        _connector = aiohttp.TCPConnector(ssl=False)
        _auth = aiohttp.BasicAuth(self.user, self.password)
        self._session = aiohttp.ClientSession(
            self.endpoint,
            connector=_connector,
            auth=_auth,
            # raise_for_status=True,
        )

    async def aclose(self) -> None:
        await self._session.close()

    @contextlib.asynccontextmanager
    async def send_request(
        self,
        method: str,
        path: str,
        params: dict[str, str | int] | None = None,
        data: dict[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        async with self._session.request(method=method, url=path, params=params, json=data) as resp:
            yield resp

    async def wait_job(self, job_id: str) -> AsyncJobResult:
        while True:
            async with self.send_request("get", f"/api/cluster/jobs/{job_id}") as resp:
                data = await resp.json()
                match data["state"]:
                    case "running":
                        await asyncio.sleep(0.1)
                        continue
                    case "failure":
                        error_code = data["error"]["code"]
                        error_msg = data["error"]["message"]
                    case _:
                        error_code = None
                        error_msg = None
                return {
                    "state": data["state"],
                    "code": error_code,
                    "message": error_msg,
                }

    @staticmethod
    def check_job_result(result: AsyncJobResult, allowed_codes: Iterable[JobResponseCode]) -> None:
        _allowed_codes = {code.value for code in allowed_codes}
        if result["state"] == "failure":
            if result["code"] in _allowed_codes:
                pass
            else:
                raise NetAppClientError(f"{result['state']} [{result['code']}] {result['message']}")

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
        default_extra_fields = ["nas.path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self.send_request(
            "get",
            "/api/storage/volumes",
            params={"fields": ",".join(_extra_fields)},
        ) as resp:
            data = await resp.json()
            items = {}
            for record in data["records"]:
                volume_id = VolumeID(record.pop("uuid"))
                items[volume_id] = VolumeInfo(
                    uuid=volume_id,
                    name=record.pop("name"),
                    path=Path(record.pop("nas", {}).pop("path")),
                )
                items[volume_id].update(record)
            return items

    async def get_volume_by_name(
        self,
        name: str,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> VolumeInfo:
        default_extra_fields = ["nas.path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self.send_request(
            "get",
            "/api/storage/volumes",
            params={"name": name, "fields": ",".join(_extra_fields)},
        ) as resp:
            data = await resp.json()
            record = data["records"][0]
            volume_info = VolumeInfo(
                uuid=VolumeID(record.pop("uuid")),
                name=record.pop("name"),
                path=Path(record.pop("nas", {}).pop("path")),
            )
            volume_info.update(record)
            return volume_info

    async def get_volume_by_id(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> VolumeInfo:
        default_extra_fields = ["nas.path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_id}",
            params={"fields": ",".join(_extra_fields)},
        ) as resp:
            record = await resp.json()
            volume_info = VolumeInfo(
                uuid=VolumeID(record.pop("uuid")),
                name=record.pop("name"),
                path=Path(record.pop("nas", {}).pop("path")),
            )
            volume_info.update(record)
            return volume_info

    async def get_volume_metric_by_id(
        self,
        volume_id: VolumeID,
        extra_fields: Optional[Sequence[str]] = None,
    ) -> dict[str, Any]:
        default_extra_fields = ["path"]
        _extra_fields = (
            [*default_extra_fields, *extra_fields] if extra_fields else default_extra_fields
        )
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_id}/metrics",
            params={"fields": ",".join(_extra_fields)},
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
        async with self.send_request(
            "get",
            f"/api/storage/qtrees/{volume_id}",
            params={"fields": ",".join(_extra_fields)},
        ) as resp:
            data = await resp.json()
            items = []
            for record in data["records"]:
                item = QTreeInfo(
                    name=record.pop("name"),
                    id=int(record.pop("id")),
                    path=Path(record.pop("path")),
                )
                item.update(record)
                items.append(item)
            return items

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
        async with self.send_request(
            "get",
            f"/api/storage/qtrees/{volume_id}/{qtree_id}",
            params={"fields": ",".join(_extra_fields)},
        ) as resp:
            record = await resp.json()
            qtree_info = QTreeInfo(
                name=record.pop("name"),
                id=int(record.pop("id")),
                path=Path(record.pop("path")),
            )
            qtree_info.update(record)
            return qtree_info

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
        async with self.send_request(
            "get",
            "/api/storage/qtrees",
            params={
                "name": name,
                "volume.uuid": str(volume_id),
                "fields": ",".join(_extra_fields),
            },
        ) as resp:
            data = await resp.json()
            if data["num_records"] > 0:
                record = data["records"][0]
                qtree_info = QTreeInfo(
                    name=record.pop("name"),
                    id=int(record.pop("id")),
                    path=Path(record.pop("path")),
                )
                qtree_info.update(record)
                return qtree_info
            else:
                raise RuntimeError(f"No qtree {name} found in the volume {volume_id}")

    async def create_qtree(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
    ) -> AsyncJobResult:
        async with self.send_request(
            "post",
            "/api/storage/qtrees",
            data={
                "svm.uuid": str(svm_id),
                "volume.uuid": str(volume_id),
                "name": qtree_name,
                "user.id": self.user_id,
                "group.id": self.group_id,
            },
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def set_quota_rule(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
        config: QuotaConfig,
    ) -> AsyncJobResult:
        async with self.send_request(
            "post",
            "/api/storage/quota/rules",
            data={
                "svm.uuid": str(svm_id),
                "volume.uuid": str(volume_id),
                "type": "tree",
                "qtree.name": qtree_name,
                "space": {
                    "hard_limit": config.limit_bytes,
                    "soft_limit": config.limit_bytes,
                },
                # 'files': {  # not supported yet from Backend.AI
                #     'hard_limit': 0,
                #     'soft_limit': 0,
                # },
            },
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def _find_quota_rule(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
    ) -> dict[str, Any]:
        async with self.send_request(
            "get",
            "/api/storage/quota/rules",
            params={
                "svm.uuid": str(svm_id),
                "volume.uuid": str(volume_id),
                "type": "tree",
                "qtree.name": qtree_name,
                "fields": "space,files",
            },
        ) as resp:
            data = await resp.json()
            records = data["records"]
            if data["num_records"] == 0:
                raise NetAppClientError(
                    f"Quota rule not found for the volume {volume_id} and the qtree {qtree_name}"
                )
            return records[0]

    async def update_quota_rule(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
        config: QuotaConfig,
    ) -> AsyncJobResult:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        async with self.send_request(
            "patch",
            f"/api/storage/quota/rules/{record['uuid']}",
            data={
                "space": {
                    "hard_limit": config.limit_bytes,
                    "soft_limit": config.limit_bytes,
                },
                # 'files': {  # not supported yet from Backend.AI
                #     'hard_limit': 0,
                #     'soft_limit': 0,
                # },
            },
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def get_quota_rule(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
    ) -> QuotaConfig:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        return QuotaConfig(
            limit_bytes=record["space"]["hard_limit"],
        )

    async def delete_quota_rule(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
    ) -> AsyncJobResult:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        async with self.send_request(
            "delete",
            f"/api/storage/quota/rules/{record['uuid']}",
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def enable_quota(
        self,
        volume_id: VolumeID,
        enable: bool = True,
    ) -> AsyncJobResult:
        async with self.send_request(
            "patch",
            f"/api/storage/volumes/{volume_id}",
            data={
                "quota.enabled": enable,
            },
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def get_quota_report(
        self,
        svm_id: StorageID,
        volume_id: VolumeID,
        qtree_name: str,
    ) -> QuotaUsage:
        async with self.send_request(
            "get",
            "/api/storage/quota/reports",
            params={
                "type": "tree",
                "svm.uuid": str(svm_id),
                "volume.uuid": str(volume_id),
                "qtree.name": qtree_name,
                "fields": "space",
            },
        ) as resp:
            data = await resp.json()
            records = data["records"]
            if data["num_records"] == 0:
                raise NetAppClientError(
                    f"Quota report not found for the volume {volume_id} and the qtree {qtree_name}"
                )
            return QuotaUsage(
                used_bytes=records[0]["space"]["used"]["total"],
                limit_bytes=records[0]["space"]["hard_limit"],
            )

    async def get_qos_policies(self) -> List[Mapping[str, Any]]:
        async with self.send_request(
            "get",
            "/api/storage/qos/policies",
        ) as resp:
            data = await resp.json()
            qos_policies_metadata = data["records"]
            qos_policies = []
            for qos in qos_policies_metadata:
                policy = await self.get_qos_by_uuid(qos["uuid"])
                qos_policies.append(policy)
        return qos_policies

    async def get_qos_by_uuid(self, qos_uuid) -> Mapping[str, Any]:
        async with self.send_request(
            "get",
            f"/api/storage/qos/policies/{qos_uuid}",
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
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_uuid}?fields=qos",
        ) as resp:
            data = await resp.json()
        return data["qos"]

from __future__ import annotations

import asyncio
import csv
import logging
import os
import shlex
import subprocess
import time
import urllib.parse
from collections.abc import AsyncGenerator, AsyncIterator, Iterable, Sequence
from contextlib import aclosing, asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.common.clients.storage_backends.netapp.dto import (
    NetAppCluster,
    NetAppCreateQTreeRequest,
    NetAppCreateQuotaRuleRequest,
    NetAppEnableQuotaRequest,
    NetAppJobResult,
    NetAppQoSFixedPolicy,
    NetAppQoSPolicy,
    NetAppQTreeByNameQuery,
    NetAppQTreeInfo,
    NetAppQTreeListQuery,
    NetAppQTreeQuery,
    NetAppQuotaConfig,
    NetAppQuotaReportQuery,
    NetAppQuotaRule,
    NetAppQuotaRuleQuery,
    NetAppQuotaUsage,
    NetAppSVMInfo,
    NetAppUpdateQuotaRuleRequest,
    NetAppVolumeByNameQuery,
    NetAppVolumeInfo,
    NetAppVolumeListQuery,
    NetAppVolumeMetric,
    NetAppVolumeMetricQuery,
    NetAppVolumeQoS,
    NetAppVolumeQoSQuery,
    NetAppVolumeQuery,
    NetAppXCPEntry,
    NetAppXCPStat,
    NetAppXCPTreeUsage,
)
from ai.backend.common.clients.storage_backends.netapp.exceptions import (
    NetAppClientError,
    NetAppQTreeNotFoundError,
    NetAppXCPExecutionError,
    NetAppXCPInvalidPathError,
    NetAppXCPOutputNotAvailableError,
)
from ai.backend.common.clients.storage_backends.netapp.types import (
    NetAppJobResponseCode,
    NetAppXCPEntryType,
)
from ai.backend.common.types import BinarySize
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


def _to_volume_info(record: dict[str, Any]) -> NetAppVolumeInfo:
    volume_id = UUID(record.pop("uuid"))
    name = record.pop("name")
    path = Path(record.pop("nas", {}).pop("path"))
    return NetAppVolumeInfo.model_validate({
        **record,
        "uuid": volume_id,
        "name": name,
        "path": path,
    })


def _to_qtree_info(record: dict[str, Any]) -> NetAppQTreeInfo:
    name = record.pop("name")
    qtree_id = int(record.pop("id"))
    path = Path(record.pop("path"))
    return NetAppQTreeInfo.model_validate({**record, "id": qtree_id, "name": name, "path": path})


def _with_extra_fields(default_fields: list[str], extra_fields: Sequence[str] | None) -> list[str]:
    return [*default_fields, *extra_fields] if extra_fields else default_fields


@dataclass
class NetAppClientArgs:
    endpoint: str
    user: str
    password: str


class NetAppClient:
    """NetApp ONTAP REST API client using HTTP basic auth."""

    _endpoint: str
    _user: str
    _password: str
    _session: aiohttp.ClientSession

    def __init__(self, args: NetAppClientArgs) -> None:
        self._endpoint = args.endpoint
        self._user = args.user
        self._password = args.password
        self._session = aiohttp.ClientSession(
            self._endpoint,
            connector=aiohttp.TCPConnector(ssl=False),
            auth=aiohttp.BasicAuth(self._user, self._password),
        )

    async def aclose(self) -> None:
        await self._session.close()

    @asynccontextmanager
    async def send_request(
        self,
        method: str,
        path: str,
        params: dict[str, str | int] | None = None,
        data: dict[str, Any] | None = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        async with self._session.request(method=method, url=path, params=params, json=data) as resp:
            yield resp

    async def wait_job(self, job_id: str) -> NetAppJobResult:
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
            return NetAppJobResult(state=data["state"], code=error_code, message=error_msg)

    @staticmethod
    def check_job_result(
        result: NetAppJobResult, allowed_codes: Iterable[NetAppJobResponseCode]
    ) -> None:
        _allowed_codes = {code.value for code in allowed_codes}
        if result.state == "failure" and result.code not in _allowed_codes:
            raise NetAppClientError(f"{result.state} [{result.code}] {result.message}")

    async def get_cluster(self) -> NetAppCluster:
        async with self.send_request("get", "/api/cluster") as resp:
            data = await resp.json()
        return NetAppCluster(
            cluster_name=data["name"],
            cluster_uuid=data["uuid"],
            version=data["version"]["full"],
        )

    async def list_volumes(
        self, extra_fields: Sequence[str] | None = None
    ) -> list[NetAppVolumeInfo]:
        async with self.send_request(
            "get",
            "/api/storage/volumes",
            params=NetAppVolumeListQuery(
                fields=_with_extra_fields(["nas.path"], extra_fields)
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return [_to_volume_info(record) for record in data["records"]]

    async def get_volume_by_name(
        self,
        name: str,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppVolumeInfo:
        async with self.send_request(
            "get",
            "/api/storage/volumes",
            params=NetAppVolumeByNameQuery(
                name=name, fields=_with_extra_fields(["nas.path"], extra_fields)
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return _to_volume_info(data["records"][0])

    async def get_volume_by_id(
        self,
        volume_id: UUID,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppVolumeInfo:
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_id}",
            params=NetAppVolumeQuery(
                fields=_with_extra_fields(["nas.path"], extra_fields)
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            record = await resp.json()
        return _to_volume_info(record)

    async def get_volume_metric_by_id(
        self,
        volume_id: UUID,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppVolumeMetric:
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_id}/metrics",
            params=NetAppVolumeMetricQuery(
                fields=_with_extra_fields(["path"], extra_fields)
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return NetAppVolumeMetric.model_validate(data)

    async def list_qtrees(
        self,
        volume_id: UUID,
        extra_fields: Sequence[str] | None = None,
    ) -> list[NetAppQTreeInfo]:
        async with self.send_request(
            "get",
            f"/api/storage/qtrees/{volume_id}",
            params=NetAppQTreeListQuery(
                fields=_with_extra_fields(["path"], extra_fields)
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return [_to_qtree_info(record) for record in data["records"]]

    async def get_default_qtree(
        self,
        volume_id: UUID,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppQTreeInfo:
        return await self.get_qtree_by_id(volume_id, 0, extra_fields=extra_fields)

    async def get_qtree_by_id(
        self,
        volume_id: UUID,
        qtree_id: int,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppQTreeInfo:
        async with self.send_request(
            "get",
            f"/api/storage/qtrees/{volume_id}/{qtree_id}",
            params=NetAppQTreeQuery(fields=_with_extra_fields(["path"], extra_fields)).model_dump(
                mode="json", by_alias=True
            ),
        ) as resp:
            record = await resp.json()
        return _to_qtree_info(record)

    async def get_qtree_by_name(
        self,
        volume_id: UUID,
        name: str,
        extra_fields: Sequence[str] | None = None,
    ) -> NetAppQTreeInfo:
        async with self.send_request(
            "get",
            "/api/storage/qtrees",
            params=NetAppQTreeByNameQuery(
                name=name,
                volume_uuid=volume_id,
                fields=_with_extra_fields(["path"], extra_fields),
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        if data["num_records"] > 0:
            return _to_qtree_info(data["records"][0])
        raise NetAppQTreeNotFoundError(f"No qtree {name} found in the volume {volume_id}")

    async def create_qtree(self, request: NetAppCreateQTreeRequest) -> NetAppJobResult:
        async with self.send_request(
            "post",
            "/api/storage/qtrees",
            data=request.model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def set_quota_rule(self, request: NetAppCreateQuotaRuleRequest) -> NetAppJobResult:
        async with self.send_request(
            "post",
            "/api/storage/quota/rules",
            data=request.model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def _find_quota_rule(
        self,
        svm_id: UUID,
        volume_id: UUID,
        qtree_name: str,
    ) -> NetAppQuotaRule:
        async with self.send_request(
            "get",
            "/api/storage/quota/rules",
            params=NetAppQuotaRuleQuery(
                svm_uuid=svm_id,
                volume_uuid=volume_id,
                qtree_name=qtree_name,
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        if data["num_records"] == 0:
            raise NetAppClientError(
                f"Quota rule not found for the volume {volume_id} and the qtree {qtree_name}"
            )
        return NetAppQuotaRule.model_validate(data["records"][0])

    async def update_quota_rule(
        self,
        svm_id: UUID,
        volume_id: UUID,
        qtree_name: str,
        request: NetAppUpdateQuotaRuleRequest,
    ) -> NetAppJobResult:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        async with self.send_request(
            "patch",
            f"/api/storage/quota/rules/{record.uuid}",
            data=request.model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def get_quota_rule(
        self,
        svm_id: UUID,
        volume_id: UUID,
        qtree_name: str,
    ) -> NetAppQuotaConfig:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        if record.space is None or record.space.hard_limit is None:
            raise NetAppClientError(
                f"Quota rule has no hard limit for the volume {volume_id} and the qtree {qtree_name}"
            )
        return NetAppQuotaConfig(limit_bytes=record.space.hard_limit)

    async def delete_quota_rule(
        self,
        svm_id: UUID,
        volume_id: UUID,
        qtree_name: str,
    ) -> NetAppJobResult:
        record = await self._find_quota_rule(svm_id, volume_id, qtree_name)
        async with self.send_request(
            "delete",
            f"/api/storage/quota/rules/{record.uuid}",
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def enable_quota(
        self,
        volume_id: UUID,
        request: NetAppEnableQuotaRequest,
    ) -> NetAppJobResult:
        async with self.send_request(
            "patch",
            f"/api/storage/volumes/{volume_id}",
            data=request.model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        return await self.wait_job(data["job"]["uuid"])

    async def get_quota_report(
        self,
        svm_id: UUID,
        volume_id: UUID,
        qtree_name: str,
    ) -> NetAppQuotaUsage:
        async with self.send_request(
            "get",
            "/api/storage/quota/reports",
            params=NetAppQuotaReportQuery(
                svm_uuid=svm_id,
                volume_uuid=volume_id,
                qtree_name=qtree_name,
            ).model_dump(mode="json", by_alias=True),
        ) as resp:
            data = await resp.json()
        if data["num_records"] == 0:
            raise NetAppClientError(
                f"Quota report not found for the volume {volume_id} and the qtree {qtree_name}"
            )
        records = data["records"]
        used_bytes = records[0]["space"]["used"]["total"]
        limit_bytes = records[0]["space"]["hard_limit"]
        if used_bytes < 0 or limit_bytes < 0:
            log.warning(
                "negative quota usage reported",
                used_bytes=used_bytes,
                limit_bytes=limit_bytes,
                svm_id=str(svm_id),
                netapp_volume_id=str(volume_id),
                qtree_name=qtree_name,
                response_body=str(data),
            )
        return NetAppQuotaUsage(used_bytes=used_bytes, limit_bytes=limit_bytes)

    async def get_qos_policies(self) -> list[NetAppQoSPolicy]:
        async with self.send_request(
            "get",
            "/api/storage/qos/policies",
        ) as resp:
            data = await resp.json()
        return [await self.get_qos_by_uuid(qos["uuid"]) for qos in data["records"]]

    async def get_qos_by_uuid(self, qos_uuid: str) -> NetAppQoSPolicy:
        async with self.send_request(
            "get",
            f"/api/storage/qos/policies/{qos_uuid}",
        ) as resp:
            data = await resp.json()
        fixed = data["fixed"]
        return NetAppQoSPolicy(
            uuid=data["uuid"],
            name=data["name"],
            fixed=NetAppQoSFixedPolicy(
                max_throughput_iops=fixed.get("max_throughput_iops", 0),
                max_throughput_mbps=fixed.get("max_throughput_mbps", 0),
                min_throughput_iops=fixed.get("min_throughput_iops", 0),
                min_throughput_mbps=fixed.get("min_throughput_mbps", 0),
                capacity_shared=fixed["capacity_shared"],
            ),
            svm=NetAppSVMInfo.model_validate(data["svm"]),
        )

    async def get_qos_by_volume_id(self, volume_uuid: str) -> NetAppVolumeQoS:
        async with self.send_request(
            "get",
            f"/api/storage/volumes/{volume_uuid}?{urllib.parse.urlencode(NetAppVolumeQoSQuery().model_dump(mode='json', by_alias=True))}",
        ) as resp:
            data = await resp.json()
        return NetAppVolumeQoS.model_validate(data["qos"])


_XCP_ERROR_MSG_PREFIX = b"xcp: ERROR: "


async def _spawn_and_watch(
    cmdargs: Sequence[str | bytes],
    *,
    tail_length: int = 50,
) -> AsyncGenerator[bytes, None]:
    last_lines: list[bytes] = []
    proc = await asyncio.create_subprocess_exec(
        *cmdargs,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        if proc.stdout is None:
            raise NetAppXCPOutputNotAvailableError("Subprocess stdout is not available")
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            if len(last_lines) > tail_length:
                last_lines.pop(0)
            last_lines.append(line)
            yield line.rstrip()
    finally:
        exit_code = await proc.wait()
    if exit_code != 0:
        raise NetAppXCPExecutionError(
            f"Command '{shlex.join(map(os.fsdecode, cmdargs))}' returned non-zero exit status {exit_code}.",
            extra_data={"output": b"".join(last_lines).decode(errors="replace")},
        )


@dataclass
class NetAppXCPClientArgs:
    xcp_cmd: Sequence[str]
    nfs_host: str
    nas_path: Path
    mount_path: Path
    license_check_path: Path = field(
        default_factory=lambda: Path("/tmp/backend.ai/storage.netapp.xcp-license-check")
    )


class NetAppXCPClient:
    """Runs the NetApp XCP CLI against ``<nfs_host>:<nas_path>`` for paths under ``mount_path``."""

    _xcp_cmd: list[str | bytes]
    _nfs_host: str
    _nas_path: Path
    _mount_path: Path
    _license_check_path: Path

    def __init__(self, args: NetAppXCPClientArgs) -> None:
        self._xcp_cmd = list(args.xcp_cmd)
        self._nfs_host = args.nfs_host
        self._nas_path = args.nas_path
        self._mount_path = args.mount_path
        self._license_check_path = args.license_check_path

    def _nfspath(self, relpath: Path) -> str:
        return f"{self._nfs_host}:{self._nas_path}/{relpath}"

    async def check_license(self) -> bool:
        lic_check_path = self._license_check_path
        if lic_check_path.exists() and lic_check_path.stat().st_mtime >= time.time() - 3600:
            return lic_check_path.read_bytes().strip() == b"1"
        try:
            proc = await asyncio.create_subprocess_exec(
                *[*self._xcp_cmd, b"license"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
        except FileNotFoundError:
            return False
        result = b"License status: ACTIVE\n" in stdout
        lic_check_path.parent.mkdir(parents=True, exist_ok=True)
        if result:
            lic_check_path.write_bytes(b"1")
        else:
            lic_check_path.write_bytes(b"0")
        return result

    async def copy_tree(self, src_path: Path, dst_path: Path) -> None:
        if not src_path.is_relative_to(self._mount_path):
            raise NetAppXCPInvalidPathError(f"Invalid path inside the volume: {src_path}")
        if not dst_path.is_relative_to(self._mount_path):
            raise NetAppXCPInvalidPathError(f"Invalid path inside the volume: {dst_path}")
        src_nfspath = self._nfspath(src_path.relative_to(self._mount_path))
        dst_nfspath = self._nfspath(dst_path.relative_to(self._mount_path))
        copy_cmd = [
            *self._xcp_cmd,
            b"copy",
            os.fsencode(src_nfspath),
            os.fsencode(dst_nfspath),
        ]
        async with aclosing(_spawn_and_watch(copy_cmd)) as ag:
            async for _ in ag:
                pass

    async def delete_tree(self, path: Path) -> None:
        nfspath = self._nfspath(path.relative_to(self._mount_path))
        delete_cmd = [
            *self._xcp_cmd,
            b"delete",
            b"-force",
            b"-removetopdir",
            os.fsencode(nfspath),
        ]
        async with aclosing(_spawn_and_watch(delete_cmd)) as ag:
            async for _ in ag:
                pass

    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[NetAppXCPEntry]:
        target_relpath = path.relative_to(self._mount_path)
        scan_cmd = [
            *self._xcp_cmd,
            b"scan",
            b"-fmt",
            rb"'{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}'.format(mode,uid,gid,ctime,mtime,type,size,x)",
            os.fsencode(self._nfspath(target_relpath)),
        ]

        async def aiter() -> AsyncIterator[NetAppXCPEntry]:
            proc = await asyncio.create_subprocess_exec(
                *scan_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stderr_lines: list[bytes] = []
            entry_queue: asyncio.Queue[NetAppXCPEntry | None] = asyncio.Queue(maxsize=1024)

            async def read_stdout() -> None:
                if proc.stdout is None:
                    raise NetAppXCPOutputNotAvailableError(
                        "xcp scan process stdout is not available"
                    )
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        await entry_queue.put(None)
                        break
                    if b"\0" not in line:
                        continue
                    parts = tuple(map(os.fsdecode, line.rstrip(b"\n").split(b"\0")))
                    item_path = Path(*Path(parts[7]).parts[2:])
                    inner_relpath = item_path.relative_to(target_relpath)
                    if inner_relpath == Path():
                        continue
                    item_abspath = self._mount_path / target_relpath / inner_relpath
                    match int(parts[5]):
                        case 2:
                            entry_type = NetAppXCPEntryType.DIRECTORY
                        case 5:
                            entry_type = NetAppXCPEntryType.SYMLINK
                        case _:
                            entry_type = NetAppXCPEntryType.FILE
                    symlink_target = ""
                    if entry_type == NetAppXCPEntryType.SYMLINK:
                        try:
                            symlink_dst = Path(item_abspath).resolve()
                            symlink_dst = symlink_dst.relative_to(path)
                        except (ValueError, RuntimeError):
                            pass
                        else:
                            symlink_target = os.fsdecode(symlink_dst)
                    await entry_queue.put(
                        NetAppXCPEntry(
                            name=item_path.name,
                            path=inner_relpath,
                            type=entry_type,
                            stat=NetAppXCPStat(
                                size=int(parts[6]),
                                owner=parts[1],
                                mode=int(parts[0]),
                                modified=datetime.fromtimestamp(float(parts[4]), tz=UTC),
                                created=datetime.fromtimestamp(float(parts[3]), tz=UTC),
                            ),
                            symlink_target=symlink_target,
                        ),
                    )

            async def read_stderr() -> None:
                if proc.stderr is None:
                    raise NetAppXCPOutputNotAvailableError(
                        "xcp scan process stderr is not available"
                    )
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    stderr_lines.append(line)

            try:
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(read_stdout())
                    tg.create_task(read_stderr())
                    while True:
                        item = await entry_queue.get()
                        try:
                            if item is None:
                                break
                            yield item
                        finally:
                            entry_queue.task_done()
            finally:
                await proc.wait()
            if proc.returncode != 0:
                error_msg = "unknown"
                for line in stderr_lines:
                    if line.startswith(_XCP_ERROR_MSG_PREFIX):
                        error_msg = line.removeprefix(_XCP_ERROR_MSG_PREFIX).decode()
                        break
                raise NetAppXCPExecutionError(f"Running XCP has failed: {error_msg}")

        return aiter()

    async def scan_tree_usage(self, path: Path) -> NetAppXCPTreeUsage:
        """Returns -1 for both counts when the scan exceeds 30 seconds."""
        target_relpath = path.relative_to(self._mount_path)
        total_size = 0
        total_count = 0
        scan_cmd = [*self._xcp_cmd, b"scan", b"-csv", os.fsencode(self._nfspath(target_relpath))]
        proc = await asyncio.create_subprocess_exec(
            *scan_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            async with asyncio.timeout(30):
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    reader = csv.reader(b.decode() for b in stdout.splitlines())
                    for row in reader:
                        if len(row) < 2:
                            continue
                        match row[0].lower():
                            case "total count":
                                total_count = int(row[1])
                            case "total space used":
                                total_size = int(row[1])
                            case _:
                                pass
                else:
                    error_msg = "unknown"
                    for line in stderr.splitlines():
                        if line.startswith(_XCP_ERROR_MSG_PREFIX):
                            error_msg = line.removeprefix(_XCP_ERROR_MSG_PREFIX).rstrip().decode()
                            break
                    raise NetAppXCPExecutionError(f"Running XCP has failed: {error_msg}")
        except TimeoutError:
            total_size = -1
            total_count = -1
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
        return NetAppXCPTreeUsage(file_count=total_count, used_bytes=total_size)

    async def scan_tree_size(self, path: Path) -> BinarySize:
        usage = await self.scan_tree_usage(path)
        return BinarySize(usage.used_bytes)

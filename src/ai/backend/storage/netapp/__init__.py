from __future__ import annotations

import asyncio
import csv
import logging
import os
import shlex
import subprocess
import time
from collections.abc import AsyncIterator
from contextlib import aclosing
from pathlib import Path
from typing import (
    Any,
    FrozenSet,
    Optional,
)

import aiofiles
import aiofiles.os
from tenacity import (
    AsyncRetrying,
    RetryError,
    TryAgain,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID

from ..abc import (
    CAP_FAST_FS_SIZE,
    CAP_FAST_SIZE,
    CAP_METRIC,
    CAP_QUOTA,
    CAP_VFOLDER,
    AbstractFSOpModel,
    AbstractQuotaModel,
)
from ..exception import (
    ExecutionError,
    InvalidQuotaScopeError,
    NotEmptyError,
    QuotaScopeNotFoundError,
)
from ..subproc import spawn_and_watch
from ..types import (
    SENTINEL,
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    Sentinel,
    Stat,
    TreeUsage,
)
from ..utils import fstime2datetime
from ..vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume
from .netappclient import JobResponseCode, NetAppClient, StorageID, VolumeID

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]
xcp_lic_check_path = Path("/tmp/backend.ai/storage.netapp.xcp-license-check")


class QTreeQuotaModel(BaseQuotaModel):
    """
    Implements the quota scope model using NetApp's QTrees.
    """

    def __init__(
        self,
        mount_path: Path,
        netapp_client: NetAppClient,
        svm_id: StorageID,
        volume_id: VolumeID,
    ) -> None:
        super().__init__(mount_path)
        self.netapp_client = netapp_client
        self.svm_id = svm_id
        self.volume_id = volume_id
        self.quota_enabled: bool = False

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        result = await self.netapp_client.create_qtree(self.svm_id, self.volume_id, qspath.name)
        self.netapp_client.check_job_result(result, [])

        # Ensure the quota scope path is successfully created
        try:
            async for attempt in AsyncRetrying(
                wait=wait_fixed(0.1),
                stop=stop_after_attempt(30),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    if not qspath.exists():
                        raise TryAgain
        except RetryError:
            raise QuotaScopeNotFoundError

        if options is not None:
            result = await self.netapp_client.set_quota_rule(
                self.svm_id,
                self.volume_id,
                qspath.name,
                options,
            )
            self.netapp_client.check_job_result(result, [])
            if not self.quota_enabled:
                result = await self.netapp_client.enable_quota(self.volume_id)
                self.netapp_client.check_job_result(
                    result, [JobResponseCode.QUOTA_ALEADY_ENABLED]
                )  # pass if "already on"
                self.quota_enabled = True

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None
        return await self.netapp_client.get_quota_report(self.svm_id, self.volume_id, qspath.name)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        result = await self.netapp_client.update_quota_rule(
            self.svm_id,
            self.volume_id,
            qspath.name,
            config,
        )
        self.netapp_client.check_job_result(result, [])

    # FIXME: How do we implement unset_quota() for NetApp?
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        raise InvalidQuotaScopeError(
            "Unsetting folder limit without removing quota scope is not possible for this backend"
        )

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        # QTree and quota rule is automatically removed
        # when the corresponding directory is deleted.
        await aiofiles.os.rmdir(qspath)


class XCPFSOpModel(BaseFSOpModel):
    """
    Accelerates filesystem operations using NetApp's XCP tool.
    If the tool is not installed or its license is not available, it will gracefully fallback to the
    BaseFSOpModel's standard implementations.

    ref) https://docs.netapp.com/us-en/xcp/xcp-install-xcp.html#install-and-configure-workflow
    """

    def __init__(
        self,
        mount_path: Path,
        scandir_limit: int,
        netapp_nfs_host: str,
        netapp_xcp_cmd: str,
        nas_path: Path,
    ) -> None:
        super().__init__(mount_path, scandir_limit)
        self.netapp_nfs_host = netapp_nfs_host
        self.netapp_xcp_cmd = netapp_xcp_cmd
        self.nas_path = nas_path

    async def check_license(self) -> bool:
        if xcp_lic_check_path.exists() and xcp_lic_check_path.stat().st_mtime >= time.time() - 3600:
            return xcp_lic_check_path.read_bytes().strip() == b"1"
        try:
            proc = await asyncio.create_subprocess_exec(
                *[*self.netapp_xcp_cmd, b"license"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
        except FileNotFoundError:
            return False
        result = b"License status: ACTIVE\n" in stdout
        xcp_lic_check_path.parent.mkdir(parents=True, exist_ok=True)
        if result:
            xcp_lic_check_path.write_bytes(b"1")
        else:
            xcp_lic_check_path.write_bytes(b"0")
        return result

    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        if not src_path.is_relative_to(self.mount_path):
            raise ValueError(f"Invalid path inside the volume: {src_path}")
        if not dst_path.is_relative_to(self.mount_path):
            raise ValueError(f"Invalid path inside the volume: {dst_path}")

        # Rearrange the paths into the NFS absolute path.
        # These relative paths contains the qtree (quota-scope) name as the first part.
        src_relpath = src_path.relative_to(self.mount_path)
        dst_relpath = dst_path.relative_to(self.mount_path)
        src_nfspath = f"{self.netapp_nfs_host}:{self.nas_path}/{src_relpath}"
        dst_nfspath = f"{self.netapp_nfs_host}:{self.nas_path}/{dst_relpath}"

        copy_cmd = [
            *self.netapp_xcp_cmd,
            b"copy",
            os.fsencode(src_nfspath),
            os.fsencode(dst_nfspath),
        ]
        async with aclosing(spawn_and_watch(copy_cmd)) as ag:
            async for line in ag:
                # TODO: line for bgtask
                pass

    async def delete_tree(self, path: Path) -> None:
        relpath = path.relative_to(self.mount_path)
        nfspath = f"{self.netapp_nfs_host}:{self.nas_path}/{relpath}"
        delete_cmd = [
            *self.netapp_xcp_cmd,
            b"delete",
            b"-force",
            b"-removetopdir",
            os.fsencode(nfspath),
        ]
        async with aclosing(spawn_and_watch(delete_cmd)) as ag:
            async for line in ag:
                # TODO: line for bgtask
                pass

    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        target_relpath = path.relative_to(self.mount_path)
        nfspath = f"{self.netapp_nfs_host}:{self.nas_path}/{target_relpath}"
        # Use a custom formatting
        scan_cmd = [
            *self.netapp_xcp_cmd,
            b"scan",
            b"-fmt",
            rb"'{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}'.format(mode,uid,gid,ctime,mtime,type,size,x)",
            os.fsencode(nfspath),
        ]

        async def aiter() -> AsyncIterator[DirEntry]:
            proc = await asyncio.create_subprocess_exec(
                *scan_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stderr_lines: list[bytes] = []
            entry_queue: asyncio.Queue[DirEntry | Sentinel] = asyncio.Queue(maxsize=1024)

            async def read_stdout() -> None:
                assert proc.stdout is not None
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        await entry_queue.put(SENTINEL)
                        break
                    if b"\0" not in line:
                        # This is some unexpected output like
                        # "Error while sending previously unsent statistics"
                        continue
                    parts = tuple(map(os.fsdecode, line.rstrip(b"\n").split(b"\0")))
                    item_path = Path(*Path(parts[7]).parts[2:])
                    inner_relpath = item_path.relative_to(target_relpath)
                    if inner_relpath == Path("."):  # exclude the top dir
                        continue
                    item_abspath = self.mount_path / target_relpath / inner_relpath
                    match int(parts[5]):
                        case 2:
                            entry_type = DirEntryType.DIRECTORY
                        case 5:
                            entry_type = DirEntryType.SYMLINK
                        case _:
                            entry_type = DirEntryType.FILE
                    symlink_target = ""
                    if entry_type == DirEntryType.SYMLINK:
                        try:
                            symlink_dst = Path(item_abspath).resolve()
                            symlink_dst = symlink_dst.relative_to(path)
                        except (ValueError, RuntimeError):
                            pass
                        else:
                            symlink_target = os.fsdecode(symlink_dst)
                    await entry_queue.put(
                        DirEntry(
                            name=item_path.name,
                            path=inner_relpath,
                            type=entry_type,
                            stat=Stat(
                                size=int(parts[6]),
                                owner=parts[1],
                                mode=int(parts[0]),
                                modified=fstime2datetime(float(parts[4])),
                                created=fstime2datetime(float(parts[3])),
                            ),
                            symlink_target=symlink_target,
                        ),
                    )

            async def read_stderr() -> None:
                assert proc.stderr is not None
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
                            if item is SENTINEL:
                                break
                            yield item
                        finally:
                            entry_queue.task_done()
            finally:
                await proc.wait()
            if proc.returncode != 0:
                error_msg_prefix = b"xcp: ERROR: "
                error_msg = "unknown"
                for line in stderr_lines:
                    if line.startswith(error_msg_prefix):
                        error_msg = line.removeprefix(error_msg_prefix).decode()
                        break
                raise ExecutionError(f"Running XCP has failed: {error_msg}")

        return aiter()

    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        target_relpath = path.relative_to(self.mount_path)
        nfspath = f"{self.netapp_nfs_host}:{self.nas_path}/{target_relpath}"
        total_size = 0
        total_count = 0
        # Use a tree statistics output formatting
        scan_cmd = [*self.netapp_xcp_cmd, b"scan", b"-csv", os.fsencode(nfspath)]
        proc = await asyncio.create_subprocess_exec(
            *scan_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            async with asyncio.timeout(30):
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    reader = csv.reader(map(lambda b: b.decode(), stdout.splitlines()))
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
                    error_msg_prefix = b"xcp: ERROR: "
                    error_msg = "unknown"
                    for line in stderr.splitlines():
                        if line.startswith(error_msg_prefix):
                            error_msg = line.removeprefix(error_msg_prefix).rstrip().decode()
                            break
                    raise ExecutionError(f"Running XCP has failed: {error_msg}")
        except asyncio.TimeoutError:
            # -1 indicates "too many"
            total_size = -1
            total_count = -1
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
        return TreeUsage(file_count=total_count, used_bytes=total_size)

    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        usage = await self.scan_tree_usage(path)
        return BinarySize(usage.used_bytes)


class NetAppVolume(BaseVolume):
    name = "netapp"
    ontap_endpoint: str
    netapp_user: str
    netapp_password: str
    svm_name: str
    svm_id: StorageID
    volume_name: str
    volume_id: VolumeID
    nas_path: Path

    async def create_quota_model(self) -> AbstractQuotaModel:
        return QTreeQuotaModel(
            self.mount_path,
            self.netapp_client,
            self.svm_id,
            self.volume_id,
        )

    async def create_fsop_model(self) -> AbstractFSOpModel:
        xcp_fsop_model = XCPFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
            self.netapp_nfs_host,
            self.netapp_xcp_cmd,
            self.nas_path,
        )
        if await xcp_fsop_model.check_license():
            return xcp_fsop_model
        log.warning(
            "XCP is not installed ('{}') or its license is not active. "
            "Falling back to BaseFSOpModel which may be slower.",
            shlex.join(self.netapp_xcp_cmd),
        )
        return BaseFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
        )

    async def init(self) -> None:
        self.ontap_endpoint = self.config["netapp_ontap_endpoint"]
        self.netapp_client = NetAppClient(
            self.ontap_endpoint,
            self.config["netapp_ontap_user"],
            self.config["netapp_ontap_password"],
            self.local_config["storage-proxy"]["user"],
            self.local_config["storage-proxy"]["group"],
        )
        self.netapp_nfs_host = self.config["netapp_nfs_host"]
        self.netapp_xcp_cmd = self.config["netapp_xcp_cmd"]
        self.volume_name = self.config["netapp_volume_name"]
        volume_info = await self.netapp_client.get_volume_by_name(self.volume_name, ["svm"])
        assert "svm" in volume_info
        self.volume_id = volume_info["uuid"]
        self.svm_name = volume_info["svm"]["name"]
        self.svm_id = StorageID(volume_info["svm"]["uuid"])
        self.nas_path = volume_info["path"]
        assert self.nas_path.is_absolute()
        # Example volume ID: 8a5c9938-a872-11ed-8519-d039ea42b802
        # Example volume name: "cj1nipacjssd1_02R10c1v2"
        # Example volume path: /cj1nipacjssd1_02R10c1v2/
        # Example qtree ID: 3 (default: 0)
        # Example qtree name: "quotascope1" (default: "")
        # Example qtree path: /cj1nipacjssd1_02R10c1v2/quotascope1
        # nfspath:    192.168.1.7:/cj1nipacjssd1_02R10c1v2/quotascope1/vfid[0:2]/vfid[2:4]/vfid[4:]
        # xcp_host:   ^^^^^^^^^^^
        # volume_path:            ^^^^^^^^^^^^^^^^^^^^^^^^^
        # vfpath: = mangle_vfpath(vfid)     /vfroot/mydata/quotascope1/vfid[0:2]/vfid[2:4]/vfid[4:]
        # vfroot:                           ^^^^^^^
        # mount_path:                       ^^^^^^^^^^^^^^
        # quota-scope path:                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
        # vf_relpath: = vfpath.relative_to(mount_path)     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # NOTE: QTree ID and name are per-volume.
        #       (i.e., Different volumes may have the same qtree ID and names
        #       for different QTree instances!)
        # NOTE: The default qtree in the volume has no explicit path.
        await super().init()

    async def shutdown(self) -> None:
        await self.netapp_client.aclose()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_FAST_FS_SIZE, CAP_FAST_SIZE, CAP_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        volume_info = await self.netapp_client.get_volume_by_id(self.volume_id, ["files", "quota"])
        metadata = {
            "quota": volume_info["quota"],  # type: ignore
            "files": volume_info["files"],  # type: ignore
        }
        return {"status": "healthy", "status_info": None, "metadata": metadata}

    async def get_fs_usage(self) -> CapacityUsage:
        volume_info = await self.netapp_client.get_volume_by_id(
            self.volume_id, ["space.size,space.used"]
        )
        assert "space" in volume_info
        return CapacityUsage(
            capacity_bytes=BinarySize(volume_info["space"]["size"]),
            used_bytes=BinarySize(volume_info["space"]["used"]),
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        volume_info = await self.netapp_client.get_volume_by_id(self.volume_id, ["statistics"])
        assert "statistics" in volume_info
        stats = volume_info["statistics"]
        # Example of volume info's statistics field:
        # 'statistics': {'iops_raw': {'other': 10860,
        #                             'read': 0,
        #                             'total': 10860,
        #                             'write': 0},
        #                'status': 'ok',
        #                'throughput_raw': {'other': 1239476,
        #                                   'read': 0,
        #                                   'total': 1239476,
        #                                   'write': 0},
        #                'timestamp': '2023-04-04T08:33:04Z'},
        # Example of volume metrics (default: 15s interval of last hour):
        #  {'num_records': 240,
        #   'records': [{'iops': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'latency': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'throughput': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'timestamp': '2023-04-04T08:48:30Z'},
        #               {'iops': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'latency': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'throughput': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'timestamp': '2023-04-04T08:48:15Z'},
        #               {'iops': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'latency': {'other': 66, 'read': 0, 'total': 66, 'write': 0},
        #                'throughput': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'timestamp': '2023-04-04T08:48:00Z'},
        #               {'iops': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'latency': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'throughput': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'timestamp': '2023-04-04T08:47:45Z'},
        #               {'iops': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'latency': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'throughput': {'other': 0, 'read': 0, 'total': 0, 'write': 0},
        #                'timestamp': '2023-04-04T08:47:30Z'},
        #               ...
        return FSPerfMetric(
            iops_read=stats["iops_raw"]["read"],
            iops_write=stats["iops_raw"]["write"],
            io_bytes_read=stats["throughput_raw"]["read"],
            io_bytes_write=stats["throughput_raw"]["write"],
            io_usec_read=0,
            io_usec_write=0,
        )

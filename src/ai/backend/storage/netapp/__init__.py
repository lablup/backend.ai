from __future__ import annotations

import asyncio
import glob
import json
import os
import time
from contextlib import aclosing
from pathlib import Path, PurePosixPath
from typing import FrozenSet, Optional

import aiofiles
import aiofiles.os

from ai.backend.common.types import BinarySize, HardwareMetadata

from ..abc import CAP_METRIC, CAP_VFHOST_QUOTA, CAP_VFOLDER, AbstractFSOpModel, AbstractQuotaModel
from ..exception import ExecutionError, NotEmptyError, StorageProxyError
from ..subproc import spawn_and_watch
from ..types import FSPerfMetric, FSUsage, QuotaConfig, VFolderID, VFolderUsage
from ..vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume
from .netappclient import NetAppClient, StorageID, VolumeID


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

    async def create_quota_scope(
        self,
        quota_scope_id: str,
        config: Optional[QuotaConfig] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await self.netapp_client.create_qtree(self.svm_id, self.volume_id, qspath.name)
        if config is not None:
            await self.update_quota_scope(quota_scope_id, config)

    async def get_quota_scope(
        self,
        quota_scope_id: str,
    ) -> tuple[QuotaConfig, VFolderUsage]:
        qspath = self.mangle_qspath(quota_scope_id)
        qconfig = await self.netapp_client.get_quota_rule(self.svm_id, self.volume_id, qspath.name)
        return qconfig, VFolderUsage(-1, -1)

    async def update_quota_scope(
        self,
        quota_scope_id: str,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        result = await self.netapp_client.set_quota_rule(
            self.svm_id,
            self.volume_id,
            qspath.name,
            config,
        )
        self.netapp_client.check_job_result(result, [])
        result = await self.netapp_client.enable_quota(self.volume_id)
        self.netapp_client.check_job_result(result, ["5308507"])  # pass if "already on"

    async def delete_quota_scope(
        self,
        quota_scope_id: str,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        await self.netapp_client.delete_quota_rule(
            self.svm_id,
            self.volume_id,
            qspath.name,
        )
        # QTree is automatically removed when the corresponding directory is deleted.
        await aiofiles.os.rmdir(qspath)


class XCPFSOpModel(BaseFSOpModel):
    """
    Accelerates filesystem operations using NetApp's XCP tool.

    ref) https://docs.netapp.com/us-en/xcp/xcp-install-xcp.html#install-and-configure-workflow
    """

    def __init__(
        self,
        mount_path: Path,
        netapp_xcp_host: str,
        netapp_xcp_container_name: str,
        volume_path: Path,
    ) -> None:
        super().__init__(mount_path)
        self.netapp_xcp_host = netapp_xcp_host
        self.netapp_xcp_container_name = netapp_xcp_container_name
        self.volume_path = volume_path

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
        src_nfspath = f"{self.netapp_xcp_host}:{self.volume_path}/{src_relpath}"
        dst_nfspath = f"{self.netapp_xcp_host}:{self.volume_path}/{dst_relpath}"

        copy_cmd = [b"xcp", b"copy", os.fsencode(src_nfspath), os.fsencode(dst_nfspath)]
        if self.netapp_xcp_container_name is not None:
            copy_cmd = [
                b"docker",
                b"exec",
                self.netapp_xcp_container_name.encode(),
                *copy_cmd,
            ]
        async with aclosing(spawn_and_watch(copy_cmd)) as ag:
            async for line in ag:
                # TODO: line for bgtask
                pass

    async def delete_tree(self, path: Path) -> None:
        relpath = path.relative_to(self.mount_path)
        nfspath = f"{self.netapp_xcp_host}:{self.volume_path}/{relpath}"
        delete_cmd = [b"xcp", b"delete", b"-force", os.fsencode(nfspath)]
        if self.netapp_xcp_container_name is not None:
            delete_cmd = [
                b"docker",
                b"exec",
                self.netapp_xcp_container_name.encode(),
                *delete_cmd,
            ]
        async with aclosing(spawn_and_watch(delete_cmd)) as ag:
            async for line in ag:
                # TODO: line for bgtask
                pass


class NetAppVolume(BaseVolume):
    endpoint: str
    netapp_user: str
    netapp_password: str
    svm_name: str
    svm_id: StorageID
    volume_name: str
    volume_id: VolumeID
    volume_path: Path

    def create_quota_model(self) -> AbstractQuotaModel:
        return QTreeQuotaModel(
            self.mount_path,
            self.netapp_client,
            self.svm_id,
            self.volume_id,
        )

    def create_fsop_model(self) -> AbstractFSOpModel:
        return XCPFSOpModel(
            self.mount_path,
            self.netapp_xcp_host,
            self.netapp_xcp_container_name,
            self.volume_path,
        )

    async def init(self) -> None:
        self.endpoint = self.config["netapp_endpoint"]
        self.netapp_client = NetAppClient(
            self.endpoint,
            self.config["netapp_user"],
            self.config["netapp_password"],
        )
        self.netapp_xcp_host = self.config["netapp_xcp_host"]
        self.netapp_xcp_catalog_path = self.config["netapp_xcp_catalog_path"]
        self.netapp_xcp_container_name = self.config["netapp_xcp_container_name"]
        self.volume_name = self.config["netapp_volume_name"]
        # TODO: resolve async-init ordering issue
        volume_info = await self.netapp_client.get_volume_by_name(self.volume_name, ["svm"])
        assert "svm" in volume_info
        self.volume_id = volume_info["uuid"]
        self.svm_name = volume_info["svm"]["name"]
        self.svm_id = StorageID(volume_info["svm"]["uuid"])
        self.volume_path = volume_info["path"]
        assert self.volume_path.is_absolute()
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

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_VFHOST_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        volume_info = await self.netapp_client.get_volume_by_id(self.volume_id, ["files", "quota"])
        metadata = {
            "quota": volume_info["quota"],  # type: ignore
            "files": volume_info["files"],  # type: ignore
        }
        return {"status": "healthy", "status_info": None, "metadata": metadata}

    async def get_fs_usage(self) -> FSUsage:
        volume_info = await self.netapp_client.get_volume_by_id(
            self.volume_id, ["space.size,space.used"]
        )
        assert "space" in volume_info
        return FSUsage(
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

    async def shutdown(self) -> None:
        await self.netapp_client.aclose()

    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> VFolderUsage:
        target_path = self.sanitize_vfpath(vfid, relpath)
        target_relpath = target_path.relative_to(self.mount_path)
        nfspath = f"{self.netapp_xcp_host}:{self.volume_path}/{target_relpath}"
        total_size = 0
        total_count = 0
        start_time = time.monotonic()
        available = True

        prev_files_count = 0
        curr_files_count = 0

        # check the number of scan result files changed
        # NOTE: if the target dir contains a small number of files, scan result doesn't get saved
        files = list(glob.iglob(f"{self.netapp_xcp_catalog_path}/stats/*.json"))
        prev_files_count = len(files)

        scan_cmd = ["xcp", "scan", "-q", nfspath]
        if self.netapp_xcp_container_name is not None:
            scan_cmd = ["docker", "exec", self.netapp_xcp_container_name] + scan_cmd
        # Measure the exact file sizes and bytes
        proc = await asyncio.create_subprocess_exec(
            *scan_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, stderr = await proc.communicate()
            if b"xcp: ERROR:" in stdout:
                # destination directory is busy for other operations
                if b"xcp: ERROR: mnt3 MOUNT" in stdout:
                    raise StorageProxyError
                available = False
            available = False if (await proc.wait() != 0) else True
            # get the latest saved file
            # scan command saves json file when operation completed
            files = sorted(
                glob.iglob(f"{self.netapp_xcp_catalog_path}/stats/*.json"),
                key=os.path.getctime,
                reverse=True,
            )
            curr_files_count = len(files)

            # scan result file has been created
            if prev_files_count < curr_files_count and available:
                file = files[0]
                async with aiofiles.open(file, "r", encoding="utf8") as scan_result:
                    contents = await scan_result.read()
                    data = json.loads(contents)
                    # includes size element
                    count_keys = [
                        "numberOfDirectories",
                        "numberOfHardlinkedFiles",
                        "numberOfHardlinks",
                        "numberOfRegularFiles",
                        "numberOfSpecialFiles",
                        "numberOfSymbolicLinks",
                        "numberOfUnreadableDirs",
                        "numberOfUnreadableFiles",
                    ]
                    size_keys = [
                        "spaceSavedByHardlinks",
                        "spaceUsedDirectories",
                        "spaceUsedRegularFiles",
                        "spaceUsedSpecialFiles",
                        "spaceUsedSymbolicLinks",
                    ]
                    total_count = sum([data[item] for item in count_keys])
                    total_size = sum([data[item] for item in size_keys])
            else:
                # if there's no scan result file, or cannot execute xcp command,
                # then use the same way in vfs
                def _calc_usage(target_path: os.DirEntry | Path) -> None:
                    nonlocal total_size, total_count
                    _timeout = 3
                    # FIXME: Remove "type: ignore" when python/mypy#11964 is resolved.
                    with os.scandir(target_path) as scanner:  # type: ignore
                        for entry in scanner:
                            if entry.is_dir():
                                _calc_usage(entry)
                                continue
                            if entry.is_file() or entry.is_symlink():
                                stat = entry.stat(follow_symlinks=False)
                                total_size += stat.st_size
                                total_count += 1
                            if total_count % 1000 == 0:
                                # Cancel if this I/O operation takes too much time.
                                if time.monotonic() - start_time > _timeout:
                                    raise TimeoutError

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _calc_usage, target_path)
        except StorageProxyError:
            raise ExecutionError("Storage server is busy. Please try again")
        except FileNotFoundError:
            available = False
        except IndexError:
            available = False
        except TimeoutError:
            # -1 indicates "too many"
            total_size = -1
            total_count = -1
        if not available:
            raise ExecutionError(
                "Cannot access the scan result file. Please check xcp is activated.",
            )

        return VFolderUsage(file_count=total_count, used_bytes=total_size)

    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        usage = await self.get_usage(vfid)
        return BinarySize(usage.used_bytes)

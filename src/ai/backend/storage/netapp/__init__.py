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

from ..abc import CAP_METRIC, CAP_VFHOST_QUOTA, CAP_VFOLDER
from ..exception import ExecutionError, NotEmptyError, StorageProxyError
from ..subproc import spawn_and_watch
from ..types import FSPerfMetric, FSUsage, QuotaConfig, VFolderID, VFolderUsage
from ..vfs import BaseVolume
from .netappclient import NetAppClient
from .quotamanager import QuotaManager


class NetAppVolume(BaseVolume):
    endpoint: str
    netapp_admin: str
    netapp_password: str
    netapp_svm: str
    netapp_volume_name: str
    netapp_volume_uuid: str
    netapp_qtree_name: str
    netapp_qtree_id: str

    async def init(self) -> None:
        self.endpoint = self.config["netapp_endpoint"]
        self.netapp_admin = self.config["netapp_admin"]
        self.netapp_password = str(self.config["netapp_password"])
        self.netapp_svm = self.config["netapp_svm"]
        self.netapp_volume_name = self.config["netapp_volume_name"]
        self.netapp_xcp_hostname = self.config["netapp_xcp_hostname"]
        self.netapp_xcp_catalog_path = self.config["netapp_xcp_catalog_path"]
        self.netapp_xcp_container_name = self.config["netapp_xcp_container_name"]

        self.netapp_client = NetAppClient(
            str(self.endpoint),
            self.netapp_admin,
            self.netapp_password,
            str(self.netapp_svm),
            self.netapp_volume_name,
        )

        self.quota_manager = QuotaManager(
            endpoint=str(self.endpoint),
            user=self.netapp_admin,
            password=self.netapp_password,
            svm=str(self.netapp_svm),
            volume_name=self.netapp_volume_name,
        )

        # assign qtree info after netapp_client and quotamanager are initiated
        self.netapp_volume_uuid = await self.netapp_client.get_volume_uuid_by_name()
        default_qtree = await self.netapp_client.get_default_qtree_by_volume_id(
            self.netapp_volume_uuid,
        )
        self.netapp_qtree_name = default_qtree.get(
            "name",
            self.config["netapp_qtree_name"],
        )
        self.netapp_qtree_id = await self.netapp_client.get_qtree_id_by_name(self.netapp_qtree_name)

        # adjust mount path (volume + qtree)
        self.mount_path = (self.mount_path / self.netapp_qtree_name).resolve()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_VFHOST_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        raw_metadata = await self.netapp_client.get_metadata()
        qtree_info = await self.netapp_client.get_default_qtree_by_volume_id(
            self.netapp_volume_uuid
        )
        self.netapp_qtree_name = qtree_info["name"]
        quota = await self.quota_manager.get_quota_by_qtree_name(self.netapp_qtree_name)
        # add quota in hwinfo
        metadata = {"quota": json.dumps(quota), **raw_metadata}
        return {"status": "healthy", "status_info": None, "metadata": {**metadata}}

    async def get_fs_usage(self) -> FSUsage:
        volume_usage = await self.netapp_client.get_usage()
        qtree_info = await self.netapp_client.get_default_qtree_by_volume_id(
            self.netapp_volume_uuid
        )
        self.netapp_qtree_name = qtree_info["name"]
        quota = await self.quota_manager.get_quota_by_qtree_name(self.netapp_qtree_name)
        space = quota.get("space")
        if space and space.get("hard_limit"):
            capacity_bytes = space["hard_limit"]
        else:
            capacity_bytes = volume_usage["capacity_bytes"]
        return FSUsage(
            capacity_bytes=capacity_bytes,
            used_bytes=volume_usage["used_bytes"],
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        uuid = await self.netapp_client.get_volume_uuid_by_name()
        volume_info = await self.netapp_client.get_volume_info(uuid)
        metric = volume_info["metric"]
        return FSPerfMetric(
            iops_read=metric["iops"]["read"],
            iops_write=metric["iops"]["write"],
            io_bytes_read=metric["throughput"]["read"],
            io_bytes_write=metric["throughput"]["write"],
            io_usec_read=metric["latency"]["read"],
            io_usec_write=metric["latency"]["write"],
        )

    async def delete_vfolder(self, vfid: VFolderID) -> None:
        vfpath = self.mangle_vfpath(vfid)
        vf_relpath = vfpath.relative_to(self.mount_path)
        nfs_path = f"{self.netapp_xcp_hostname}:/{self.netapp_volume_name}/{vf_relpath}"
        delete_cmd = [b"xcp", b"delete", b"-force", os.fsencode(nfs_path)]
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
        # remove intermediate prefix directories if they become empty
        await aiofiles.os.rmdir(vfpath.parent.parent)

    async def shutdown(self) -> None:
        await self.netapp_client.aclose()
        await self.quota_manager.aclose()

    # ------ volume operations ------
    async def create_quota_scope(
        self,
        quota_scope_id: str,
        config: Optional[QuotaConfig] = None,
    ) -> None:
        # qspath = self.mangle_qspath(quota_scope_id)
        # TODO: invoke the qtree creation API
        pass

    async def get_quota_scope(
        self,
        quota_scope_id: str,
    ) -> tuple[QuotaConfig, VFolderUsage]:
        # TODO: invoke the qtree quota-get API
        return QuotaConfig(0, 0), VFolderUsage(-1, -1)

    async def update_quota_scope(
        self,
        quota_scope_id: str,
        options: Optional[QuotaConfig] = None,
    ) -> QuotaConfig:
        # TODO: invoke the qtree quota-set API
        raise NotImplementedError

    async def delete_quota_scope(
        self,
        quota_scope_id: str,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        # TODO: invoke the qtree deletion API

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
        nfs_src_path = f"{self.netapp_xcp_hostname}:/{self.netapp_volume_name}/{src_relpath}"
        nfs_dst_path = f"{self.netapp_xcp_hostname}:/{self.netapp_volume_name}/{dst_relpath}"

        copy_cmd = [b"xcp", b"copy", os.fsencode(nfs_src_path), os.fsencode(nfs_dst_path)]
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

    # ------ qtree and quotas operations ------
    async def get_quota(self, vfid: VFolderID) -> BinarySize:
        raise NotImplementedError

    async def set_quota(self, vfid: VFolderID, size_bytes: BinarySize) -> None:
        raise NotImplementedError

    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> VFolderUsage:
        target_path = self.sanitize_vfpath(vfid, relpath)
        target_relpath = target_path.relative_to(self.mount_path)
        nfs_path = f"{self.netapp_xcp_hostname}:/{self.netapp_volume_name}/{target_relpath}"
        total_size = 0
        total_count = 0
        start_time = time.monotonic()
        available = True

        prev_files_count = 0
        curr_files_count = 0

        # check the number of scan result files changed
        # NOTE: if directory contains small amout of files, scan result doesn't get saved
        files = list(glob.iglob(f"{self.netapp_xcp_catalog_path}/stats/*.json"))
        prev_files_count = len(files)

        scan_cmd = ["xcp", "scan", "-q", nfs_path]
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

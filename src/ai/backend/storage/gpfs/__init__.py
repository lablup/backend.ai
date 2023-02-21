import json
import logging
from pathlib import Path, PurePath
from typing import Any, FrozenSet, Mapping, Optional
from uuid import UUID

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata
from ai.backend.storage.abc import CAP_METRIC, CAP_QUOTA, CAP_VFOLDER, AbstractVolume
from ai.backend.storage.types import FSPerfMetric, FSUsage, VFolderCreationOptions
from ai.backend.storage.vfs import BaseVolume

from ..exception import VFolderCreationError
from .exceptions import GPFSJobFailedError, GPFSNoMetricError
from .gpfs_client import GPFSAPIClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GPFSVolume(BaseVolume):

    api_client: GPFSAPIClient

    fs: str

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        fsprefix: Optional[PurePath] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(local_config, mount_path, fsprefix=fsprefix, options=options)
        verify_ssl = self.config.get("gpfs_verify_ssl", False)

        self.api_client = GPFSAPIClient(
            self.config["gpfs_endpoint"],
            self.config["gpfs_username"],
            self.config["gpfs_password"],
            # follows ssl parameter on https://docs.aiohttp.org/en/v3.7.3/client_reference.html
            ssl=False if not verify_ssl else None,
        )
        self.fs = self.config["gpfs_fs_name"]

    async def init(self) -> None:
        await super().init()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        nodes = await self.api_client.list_nodes()
        invalid_status = ["FAILED", "DEGRADED", "ERROR"]
        health_status = "HEALTHY"

        for node in nodes:
            if health_status == "ERROR":
                break
            node_health_statuses = await self.api_client.get_node_health(node)
            for status in node_health_statuses:
                if status.state in invalid_status:
                    health_status = status

        match health_status:
            case "HEALTHY":
                status = "healthy"
            case "DEGRADED":
                status = "degraded"
            case _:
                status = "unavailable"
        cluster_info = await self.api_client.get_cluster_info()
        quotas = await self.api_client.list_quotas(self.fs)
        return {
            "status": status,
            "status_info": None,
            "metadata": {
                "quota": json.dumps([q.to_json() for q in quotas]),
                "cluster_info": json.dumps(cluster_info),
            },
        }

    async def get_fs_usage(self) -> FSUsage:
        storage_pools = await self.api_client.list_fs_pools(self.fs)
        free, total = 0, 0
        for _pool in storage_pools:
            pool = await self.api_client.get_fs_pool(self.fs, _pool.storagePoolName)
            if pool.totalDataInKB is None or pool.freeDataInKB is None:
                continue
            total += pool.totalDataInKB
            free += pool.freeDataInKB
        return FSUsage(BinarySize(total), BinarySize(total - free))

    async def get_performance_metric(self) -> FSPerfMetric:
        # ref: https://www.ibm.com/docs/en/spectrum-scale/5.0.3?topic=2-perfmondata-get
        query = (
            "metrics "
            "avg(gpfs_ns_read_ops),"
            "avg(gpfs_ns_write_ops),"
            "avg(gpfs_ns_bytes_read),"
            "avg(gpfs_ns_bytes_written),"
            "avg(gpfs_ns_max_disk_wait_rd),"
            "avg(gpfs_ns_max_disk_wait_wr) "
            "last 1 "
            "bucket_size 10"
        )
        try:
            metrics = await self.api_client.get_metric(query)
            latest_metric = metrics["performanceData"]["rows"][-1]["values"]
        except (KeyError, IndexError):
            raise GPFSNoMetricError
        return FSPerfMetric(
            iops_read=latest_metric[0] or 0,
            iops_write=latest_metric[1] or 0,
            io_bytes_read=latest_metric[2] or 0,
            io_bytes_write=latest_metric[3] or 0,
            io_usec_read=latest_metric[4] or 0,
            io_usec_write=latest_metric[5] or 0,
        )

    async def create_vfolder(
        self,
        vfid: UUID,
        options: Optional[VFolderCreationOptions] = None,
        *,
        exist_ok: bool = False,
    ) -> None:
        vfpath = self.mangle_vfpath(vfid)
        await self.api_client.create_fileset(
            self.fs,
            str(vfid),
            path=vfpath,
            owner=self.config.get("gpfs_owner", "1000:1000"),
        )
        if options is not None and options.quota is not None:
            try:
                await self.set_quota(vfid, options.quota)
            except GPFSJobFailedError:
                await self.api_client.remove_fileset(self.fs, str(vfid))
                raise VFolderCreationError("Failed to set quota")

    async def clone_vfolder(
        self,
        src_vfid: UUID,
        dst_volume: AbstractVolume,
        dst_vfid: UUID,
        options: Optional[VFolderCreationOptions] = None,
    ) -> None:
        assert isinstance(dst_volume, GPFSVolume)
        await dst_volume.create_vfolder(dst_vfid, options=options)

        fs_usage = await dst_volume.get_fs_usage()
        vfolder_usage = await self.get_usage(src_vfid)
        if vfolder_usage.used_bytes > fs_usage.capacity_bytes - fs_usage.used_bytes:
            raise VFolderCreationError("Not enough space available for clone")

        # TODO: Wait until file operation is done
        await self.api_client.copy_folder(
            self.fs,
            self.mangle_vfpath(src_vfid),
            dst_volume.fs,
            dst_volume.mangle_vfpath(dst_vfid),
        )

    async def delete_vfolder(self, vfid: UUID) -> None:
        await self.api_client.remove_fileset(self.fs, str(vfid))

    async def get_quota(self, vfid: UUID) -> BinarySize:
        quotas = await self.api_client.list_fileset_quotas(self.fs, str(vfid))
        custom_defined_quotas = [q for q in quotas if not q.defaultQuota]
        if len(custom_defined_quotas) == 0:
            return BinarySize(-1)
        assert custom_defined_quotas[0].blockLimit is not None
        return BinarySize(custom_defined_quotas[0].blockLimit)

    async def set_quota(self, vfid: UUID, size_bytes: BinarySize) -> None:
        await self.api_client.set_quota(self.fs, str(vfid), size_bytes)

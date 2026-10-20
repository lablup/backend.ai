from __future__ import annotations

import logging
import os
import shlex
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any, ClassVar, override
from uuid import UUID

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

from ai.backend.common.clients.storage_backends.netapp.client import (
    NetAppClient,
    NetAppClientArgs,
    NetAppXCPClient,
    NetAppXCPClientArgs,
)
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.netapp.request import (
    NetAppCreateQTreeRequest,
    NetAppCreateQuotaRuleRequest,
    NetAppEnableQuotaRequest,
    NetAppUpdateQuotaRuleRequest,
)
from ai.backend.common.dto.clients.storage_backends.netapp.response import (
    NetAppQuotaSpaceLimit,
    NetAppXCPEntry,
)
from ai.backend.common.dto.clients.storage_backends.netapp.types import (
    NetAppJobResponseCode,
    NetAppXCPEntryType,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import (
    InvalidAPIParameters,
    InvalidQuotaScopeError,
    QuotaDirectoryNotEmptyError,
    QuotaScopeNotFoundError,
    VolumeNotInitializedError,
)
from ai.backend.storage.types import (
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    Stat,
    TreeUsage,
)
from ai.backend.storage.volumes.abc import (
    AbstractFSOpModel,
    AbstractQuotaModel,
)
from ai.backend.storage.volumes.vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume

log = StructuredLogger(logging.getLogger(__spec__.name))


class QTreeQuotaModel(BaseQuotaModel):
    """
    Implements the quota scope model using NetApp's QTrees.
    """

    netapp_client: NetAppClient
    svm_id: UUID
    volume_id: UUID
    user_id: int
    group_id: int
    quota_enabled: bool

    def __init__(
        self,
        mount_path: Path,
        netapp_client: NetAppClient,
        svm_id: UUID,
        volume_id: UUID,
        *,
        user_id: int,
        group_id: int,
    ) -> None:
        super().__init__(mount_path)
        self.netapp_client = netapp_client
        self.svm_id = svm_id
        self.volume_id = volume_id
        self.user_id = user_id
        self.group_id = group_id
        self.quota_enabled = False

    def _space_limit(self, config: QuotaConfig) -> NetAppQuotaSpaceLimit:
        return NetAppQuotaSpaceLimit(hard_limit=config.limit_bytes, soft_limit=config.limit_bytes)

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        result = await self.netapp_client.create_qtree(
            NetAppCreateQTreeRequest(
                svm_uuid=self.svm_id,
                volume_uuid=self.volume_id,
                name=qspath.name,
                user_id=self.user_id,
                group_id=self.group_id,
            )
        )
        self.netapp_client.check_job_result(result, [])

        try:
            async for attempt in AsyncRetrying(
                wait=wait_fixed(0.1),
                stop=stop_after_attempt(30),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    if not qspath.exists():
                        for sibling_path in os.scandir(qspath.parent):
                            if sibling_path.name == qspath.name:
                                break
                        else:
                            raise TryAgain
        except RetryError as e:
            raise QuotaScopeNotFoundError from e

        if options is not None:
            result = await self.netapp_client.set_quota_rule(
                NetAppCreateQuotaRuleRequest(
                    svm_uuid=self.svm_id,
                    volume_uuid=self.volume_id,
                    qtree_name=qspath.name,
                    space=self._space_limit(options),
                )
            )
            self.netapp_client.check_job_result(result, [])
            if not self.quota_enabled:
                result = await self.netapp_client.enable_quota(
                    self.volume_id, NetAppEnableQuotaRequest()
                )
                self.netapp_client.check_job_result(
                    result, [NetAppJobResponseCode.QUOTA_ALEADY_ENABLED]
                )  # pass if "already on"
                self.quota_enabled = True

    @override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None
        usage = await self.netapp_client.get_quota_report(self.svm_id, self.volume_id, qspath.name)
        return QuotaUsage(used_bytes=usage.used_bytes, limit_bytes=usage.limit_bytes)

    @override
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
            NetAppUpdateQuotaRuleRequest(space=self._space_limit(config)),
        )
        self.netapp_client.check_job_result(result, [])

    @override
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        raise InvalidQuotaScopeError(
            "Unsetting folder limit without removing quota scope is not possible for this backend"
        )

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise QuotaDirectoryNotEmptyError(
                f"Cannot delete quota scope '{quota_scope_id}': directory not empty"
            )
        await aiofiles.os.rmdir(qspath)


class XCPFSOpModel(BaseFSOpModel):
    """
    Accelerates filesystem operations using NetApp's XCP tool.

    ref) https://docs.netapp.com/us-en/xcp/xcp-install-xcp.html#install-and-configure-workflow
    """

    _entry_types: ClassVar[Mapping[NetAppXCPEntryType, DirEntryType]] = {
        NetAppXCPEntryType.FILE: DirEntryType.FILE,
        NetAppXCPEntryType.DIRECTORY: DirEntryType.DIRECTORY,
        NetAppXCPEntryType.SYMLINK: DirEntryType.SYMLINK,
    }
    _xcp_client: NetAppXCPClient

    def __init__(
        self,
        mount_path: Path,
        scandir_limit: int,
        xcp_client: NetAppXCPClient,
    ) -> None:
        super().__init__(mount_path, scandir_limit)
        self._xcp_client = xcp_client

    def _to_dir_entry(self, entry: NetAppXCPEntry) -> DirEntry:
        return DirEntry(
            name=entry.name,
            path=entry.path,
            type=self._entry_types[entry.type],
            stat=Stat(
                size=entry.stat.size,
                owner=entry.stat.owner,
                mode=entry.stat.mode,
                modified=entry.stat.modified,
                created=entry.stat.created,
            ),
            symlink_target=entry.symlink_target,
        )

    @override
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        await self._xcp_client.copy_tree(src_path, dst_path)

    @override
    async def delete_tree(self, path: Path) -> None:
        await self._xcp_client.delete_tree(path)

    @override
    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        async def _aiter() -> AsyncIterator[DirEntry]:
            async for entry in self._xcp_client.scan_tree(path, recursive=recursive):
                yield self._to_dir_entry(entry)

        return _aiter()

    @override
    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        usage = await self._xcp_client.scan_tree_usage(path)
        return TreeUsage(file_count=usage.file_count, used_bytes=usage.used_bytes)

    @override
    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        return await self._xcp_client.scan_tree_size(path)


class NetAppVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("netapp")
    _netapp_client: NetAppClient | None
    netapp_nfs_host: str
    netapp_xcp_cmd: list[str]
    svm_name: str
    svm_id: UUID
    volume_name: str
    volume_id: UUID
    nas_path: Path

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._netapp_client = None

    @property
    def netapp_client(self) -> NetAppClient:
        if self._netapp_client is None:
            raise VolumeNotInitializedError("NetApp client is not initialized")
        return self._netapp_client

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return QTreeQuotaModel(
            self.mount_path,
            self.netapp_client,
            self.svm_id,
            self.volume_id,
            user_id=self.local_config["storage-proxy"]["user"],
            group_id=self.local_config["storage-proxy"]["group"],
        )

    @override
    async def create_fsop_model(self) -> AbstractFSOpModel:
        xcp_client = NetAppXCPClient(
            NetAppXCPClientArgs(
                xcp_cmd=self.netapp_xcp_cmd,
                nfs_host=self.netapp_nfs_host,
                nas_path=self.nas_path,
                mount_path=self.mount_path,
            )
        )
        if await xcp_client.check_license():
            return XCPFSOpModel(
                self.mount_path,
                self.local_config["storage-proxy"]["scandir-limit"],
                xcp_client,
            )
        log.warning(
            "XCP unavailable, falling back to BaseFSOpModel",
            xcp_command=shlex.join(self.netapp_xcp_cmd),
        )
        return BaseFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
        )

    @override
    async def init(self) -> None:
        self._netapp_client = NetAppClient(
            NetAppClientArgs(
                endpoint=self.config["netapp_ontap_endpoint"],
                user=self.config["netapp_ontap_user"],
                password=self.config["netapp_ontap_password"],
            )
        )
        self.netapp_nfs_host = self.config["netapp_nfs_host"]
        self.netapp_xcp_cmd = list(self.config["netapp_xcp_cmd"])
        self.volume_name = self.config["netapp_volume_name"]
        volume_info = await self._netapp_client.get_volume_by_name(self.volume_name, ["svm"])
        if volume_info.svm is None:
            raise InvalidAPIParameters("Volume info does not contain svm data")
        self.volume_id = volume_info.uuid
        self.svm_name = volume_info.svm.name
        self.svm_id = UUID(volume_info.svm.uuid)
        self.nas_path = volume_info.path
        if not self.nas_path.is_absolute():
            raise InvalidAPIParameters("NAS path must be an absolute path")
        await super().init()

    @override
    async def shutdown(self) -> None:
        if self._netapp_client is not None:
            await self._netapp_client.aclose()

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([
            StorageBackendCapability.VFOLDER,
            StorageBackendCapability.FAST_FS_SIZE,
            StorageBackendCapability.FAST_SIZE,
            StorageBackendCapability.QUOTA,
            StorageBackendCapability.METRIC,
        ])

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        volume_info = await self.netapp_client.get_volume_by_id(self.volume_id, ["files", "quota"])
        extra = volume_info.model_extra or {}
        metadata = {
            "quota": dump_json_str(extra.get("quota")),
            "files": dump_json_str(extra.get("files")),
        }
        return {"status": "healthy", "status_info": None, "metadata": metadata}

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        volume_info = await self.netapp_client.get_volume_by_id(
            self.volume_id, ["space.size,space.used"]
        )
        if volume_info.space is None:
            raise InvalidAPIParameters("Volume info does not contain space data")
        return CapacityUsage(
            capacity_bytes=BinarySize(volume_info.space.size),
            used_bytes=BinarySize(volume_info.space.used),
        )

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        volume_info = await self.netapp_client.get_volume_by_id(self.volume_id, ["statistics"])
        if volume_info.statistics is None:
            raise InvalidAPIParameters("Volume info does not contain statistics data")
        stats = volume_info.statistics
        return FSPerfMetric(
            iops_read=stats["iops_raw"]["read"],
            iops_write=stats["iops_raw"]["write"],
            io_bytes_read=stats["throughput_raw"]["read"],
            io_bytes_write=stats["throughput_raw"]["write"],
            io_usec_read=0,
            io_usec_write=0,
        )

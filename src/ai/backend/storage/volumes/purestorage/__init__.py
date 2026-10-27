from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import aclosing, asynccontextmanager
from pathlib import Path
from typing import Any, ClassVar, override

from ai.backend.common.clients.storage_backends.purestorage.client import (
    PurityClient,
    PurityClientArgs,
    RapidFileToolkitClient,
    RapidFileToolkitV2Client,
    get_toolkit_version,
)
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.purestorage.response import RapidFileEntry
from ai.backend.common.dto.clients.storage_backends.purestorage.types import RapidFileEntryType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import BinarySize, HardwareMetadata
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import (
    ExternalStorageServiceError,
    MetricNotFoundError,
    PureStorageCommandFailedError,
    VolumeNotInitializedError,
)
from ai.backend.storage.types import (
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    Stat,
    TreeUsage,
)
from ai.backend.storage.volumes.abc import AbstractFSOpModel
from ai.backend.storage.volumes.vfs import BaseFSOpModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

log = StructuredLogger(logging.getLogger(__spec__.name))


class RapidFileToolsFSOpModel(BaseFSOpModel):
    _entry_types: ClassVar[Mapping[RapidFileEntryType, DirEntryType]] = {
        RapidFileEntryType.FILE: DirEntryType.FILE,
        RapidFileEntryType.DIRECTORY: DirEntryType.DIRECTORY,
        RapidFileEntryType.SYMLINK: DirEntryType.SYMLINK,
    }
    _toolkit: RapidFileToolkitClient

    def __init__(
        self,
        mount_path: Path,
        scandir_limit: int,
        toolkit: RapidFileToolkitClient,
    ) -> None:
        super().__init__(mount_path, scandir_limit)
        self._toolkit = toolkit

    def _to_dir_entry(self, entry: RapidFileEntry) -> DirEntry:
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
    async def copy_tree(self, src_path: Path, dst_path: Path) -> None:
        await self._toolkit.copy_tree(src_path, dst_path)

    @override
    async def delete_tree(self, path: Path) -> None:
        await self._toolkit.delete_tree(path)

    @override
    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        async def _aiter() -> AsyncIterator[DirEntry]:
            async for entry in self._toolkit.scan_tree(path):
                yield self._to_dir_entry(entry)

        return _aiter()

    @override
    async def scan_tree_usage(self, path: Path) -> TreeUsage:
        usage = await self._toolkit.scan_tree_usage(path)
        return TreeUsage(file_count=usage.file_count, used_bytes=usage.used_bytes)

    @override
    async def scan_tree_size(self, path: Path) -> BinarySize:
        return await self._toolkit.scan_tree_size(path)


class FlashBladeVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("purestorage")
    _toolkit_version: int | None
    _purity_client: PurityClient | None

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: WatcherClient | None = None,
        options: Mapping[str, Any] | None = None,
        volume_name: StorageVolumeName,
        status_check_config: VolumeStatusCheckConfig | None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            volume_name=volume_name,
            status_check_config=status_check_config,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
            watcher=watcher,
        )
        self._toolkit_version = None
        self._purity_client = None

    async def get_toolkit_version(self) -> int:
        if self._toolkit_version is None:
            self._toolkit_version = await get_toolkit_version()
        return self._toolkit_version

    @override
    async def create_fsop_model(self) -> AbstractFSOpModel:
        toolkit: RapidFileToolkitClient
        if (await self.get_toolkit_version()) == 2:
            toolkit = RapidFileToolkitV2Client()
        else:
            toolkit = RapidFileToolkitClient()
        return RapidFileToolsFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
            toolkit,
        )

    @override
    async def init(self) -> None:
        if (await self.get_toolkit_version()) == -1:
            raise PureStorageCommandFailedError(
                "PureStorage RapidFile Toolkit is not installed. "
                "You cannot use the PureStorage backend for the storage proxy."
            )
        self._purity_client = PurityClient(
            PurityClientArgs(
                endpoint=self.config["purity_endpoint"],
                api_token=self.config["purity_api_token"],
                api_version=self.config["purity_api_version"],
            )
        )
        await super().init()

    @override
    async def shutdown(self) -> None:
        if self._purity_client is not None:
            await self._purity_client.aclose()

    @asynccontextmanager
    async def _purity_session(self) -> AsyncIterator[PurityClient]:
        """Holds the client lock across a login and the calls using it."""
        if self._purity_client is None:
            raise VolumeNotInitializedError("Purity client is not initialized")
        client = self._purity_client
        async with client.lock():
            await client.login()
            try:
                yield client
            finally:
                client.clear_auth_token()

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset(
            [
                StorageBackendCapability.FAST_FS_SIZE,
                StorageBackendCapability.VFOLDER,
                StorageBackendCapability.METRIC,
                StorageBackendCapability.FAST_SCAN,
            ],
        )

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        async with self._purity_session() as client:
            metadata = await client.get_metadata()
        raw_metadata = metadata.model_dump(mode="json") if metadata is not None else {}
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {key: str(value) for key, value in raw_metadata.items()},
        }

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        fs_name = self.config["purity_fs_name"]
        async with self._purity_session() as client:
            usage = await client.get_usage(fs_name)
        if usage is None:
            raise ExternalStorageServiceError(f"no FlashBlade file system named {fs_name}")
        return CapacityUsage(
            capacity_bytes=usage.capacity_bytes,
            used_bytes=usage.used_bytes,
        )

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        async with (
            self._purity_session() as client,
            aclosing(client.get_nfs_metric(self.config["purity_fs_name"])) as items,
        ):
            async for item in items:
                return FSPerfMetric(
                    iops_read=int(item.reads_per_sec),
                    iops_write=int(item.writes_per_sec),
                    io_bytes_read=int(item.read_bytes_per_sec),
                    io_bytes_write=int(item.write_bytes_per_sec),
                    io_usec_read=item.usec_per_read_op,
                    io_usec_write=item.usec_per_write_op,
                )
        raise MetricNotFoundError("no metric found for the configured flashblade filesystem")

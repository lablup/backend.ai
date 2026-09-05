from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    ClassVar,
    Final,
    final,
)

from ai.backend.common.data.storage.types import VolumeName
from ai.backend.common.defs import DEFAULT_VFOLDER_PERMISSION_MODE
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import StorageProxyConfig
from ai.backend.storage.errors import InvalidSubpathError, VFolderNotFoundError
from ai.backend.storage.types import (
    CapacityUsage,
    DirEntry,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    TreeUsage,
    VFolderID,
    VolumeInfo,
)
from ai.backend.storage.volumes.health.abc import AbstractBackendProber, AbstractMountProber
from ai.backend.storage.volumes.health.probes import VolumeHealthProbes
from ai.backend.storage.volumes.health.types import VolumeHealthRecord
from ai.backend.storage.watcher import WatcherClient

# Available capabilities of a volume implementation
CAP_VFOLDER: Final = "vfolder"  # ability to create vfolder
CAP_METRIC: Final = "metric"  # ability to report disk related metrics
CAP_QUOTA: Final = "quota"  # ability to manage quota limits
# ability to scan filesystem size fast (e.g. by API)
CAP_FAST_FS_SIZE: Final = "fast-fs-size"
# ability to scan number of files in vFolder fast (e.g. by API)
CAP_FAST_SCAN: Final = "fast-scan"
# ability to scan vFolder size fast (e.g. by API)
CAP_FAST_SIZE: Final = "fast-size"

_CURRENT_DIR: Final = PurePosixPath(".")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractQuotaModel(metaclass=ABCMeta):
    @abstractmethod
    def mangle_qspath(self, ref: VFolderID | QuotaScopeID | str | None) -> Path:
        raise NotImplementedError

    @abstractmethod
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        """
        Creates a new quota scope.

        Raises `AlreadyExists` error if there is the quota scope with the same name.
        """
        raise NotImplementedError

    async def get_extra_quota_info(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> dict[str, Any] | None:
        """
        Get the information about the given volume.
        Returns None if target volume does not exist.
        """
        return None

    @abstractmethod
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        """
        Get the information about the given quota scope.
        Returns None if target quota scope does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        """
        Update the quota option of the given quota scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        """
        Lifts off quota set on given quota scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        """
        Deletes the given quota scope.

        Raises `NotEmpty` error if there are one or more vfolders inside the quota scope.
        """
        raise NotImplementedError


class AbstractFSOpModel(metaclass=ABCMeta):
    @abstractmethod
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        """
        The actual backend-specific implementation of copying
        files from a directory to another in an efficient way.
        The source and destination are in the same filesystem namespace
        but they may be on different physical media.
        """
        raise NotImplementedError

    @abstractmethod
    async def move_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_tree(
        self,
        path: Path,
    ) -> None:
        """
        Deletes all files and directories inside the given path.
        """
        raise NotImplementedError

    @abstractmethod
    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        """
        Iterates over all files within the given path recursively.
        """
        raise NotImplementedError

    @abstractmethod
    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        """
        Retrieves the number of bytes and the number of files and directories inside
        the given path, recursively.
        """
        raise NotImplementedError

    @abstractmethod
    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        """
        Retrieves the approximate number of bytes used by a directory,
        including all subdirectories and files recursively.

        This method can be implemented using :meth:`scan_tree_usage()`, but in many cases we can
        often implement this using a faster, dedicated command like ``du``.
        """
        raise NotImplementedError


class AbstractVolume[
    TMountProber: AbstractMountProber = AbstractMountProber,
    TBackendProber: AbstractBackendProber = AbstractBackendProber,
](metaclass=ABCMeta):
    quota_model: AbstractQuotaModel
    fsop_model: AbstractFSOpModel
    _mount_prober: TMountProber
    _backend_prober: TBackendProber
    name: ClassVar[str] = "undefined"

    volume_name: VolumeName
    _storage_proxy_config: StorageProxyConfig
    _health_record: VolumeHealthRecord
    _health_probes: VolumeHealthProbes

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        volume_name: VolumeName,
        storage_proxy_config: StorageProxyConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: WatcherClient | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.config = options or {}
        self.volume_name = volume_name
        self._storage_proxy_config = storage_proxy_config
        self._health_record = VolumeHealthRecord()
        self.etcd = etcd
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.watcher = watcher

    async def init(self) -> None:
        # After the subclass has set up its client, which its own init() does before
        # delegating here, so that a backend prober can be handed one.
        self._mount_prober = self.create_mount_prober()
        self._backend_prober = self.create_backend_prober(self._health_record)
        await self._capture_mount_baseline()
        self.fsop_model = await self.create_fsop_model()
        self.quota_model = await self.create_quota_model()
        self._health_probes = VolumeHealthProbes(
            self.volume_name,
            self._health_record,
            self._storage_proxy_config.volume_health,
            mount_prober=self._mount_prober,
            backend_prober=self._backend_prober,
        )
        await self._health_probes.start()

    async def shutdown(self) -> None:
        await self._health_probes.stop()

    # ------ mount and backend health -------

    @abstractmethod
    def create_mount_prober(self) -> TMountProber:
        raise NotImplementedError

    @abstractmethod
    def create_backend_prober(self, record: VolumeHealthRecord) -> TBackendProber:
        raise NotImplementedError

    def health_record(self) -> VolumeHealthRecord:
        """The latest probe results, recorded by this volume's own probe loops."""
        return self._health_record

    async def _capture_mount_baseline(self) -> None:
        """
        Lets the mount prober record what its later probes compare against.
        A failure is not fatal: the volume starts without a baseline and the first
        successful probe adopts one.
        """
        timeout = self._storage_proxy_config.volume_health.mount_probe_timeout
        try:
            async with asyncio.timeout(timeout):
                await asyncio.to_thread(self._mount_prober.capture_baseline)
        except TimeoutError:
            log.error(
                "Timed out capturing the mount baseline of {} after {}s; "
                "the volume starts without one",
                self.mount_path,
                timeout,
            )
        except OSError as e:
            log.error("Failed to capture the mount baseline of {}: {}", self.mount_path, e)

    @abstractmethod
    def info(self) -> VolumeInfo:
        raise NotImplementedError

    @abstractmethod
    async def create_quota_model(self) -> AbstractQuotaModel:
        raise NotImplementedError

    @abstractmethod
    async def create_fsop_model(self) -> AbstractFSOpModel:
        raise NotImplementedError

    @final
    def mangle_vfpath(self, vfid: VFolderID) -> Path:
        folder_id_hex = vfid.folder_id.hex
        prefix1 = folder_id_hex[0:2]
        prefix2 = folder_id_hex[2:4]
        rest = folder_id_hex[4:]
        return self.quota_model.mangle_qspath(vfid.quota_scope_id) / prefix1 / prefix2 / rest

    @final
    def sanitize_vfpath(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = _CURRENT_DIR,
    ) -> Path:
        vfpath = self.mangle_vfpath(vfid).resolve()
        if not (vfpath.exists() and vfpath.is_dir()):
            raise VFolderNotFoundError(f"VFolder not found or not a directory: {vfid}")
        target_path = (vfpath / relpath).resolve()
        if not target_path.is_relative_to(vfpath):
            raise InvalidSubpathError(vfid, relpath)
        return target_path

    @final
    def strip_vfpath(self, vfid: VFolderID, target_path: Path) -> PurePosixPath:
        vfpath = self.mangle_vfpath(vfid).resolve()
        return PurePosixPath(target_path.relative_to(vfpath))

    # ------ volume operations -------

    @abstractmethod
    async def get_capabilities(self) -> frozenset[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_hwinfo(self) -> HardwareMetadata:
        raise NotImplementedError

    @abstractmethod
    async def create_vfolder(
        self,
        vfid: VFolderID,
        exist_ok: bool = False,
        mode: int = DEFAULT_VFOLDER_PERMISSION_MODE,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_vfolder(self, vfid: VFolderID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clone_vfolder(
        self,
        src_vfid: VFolderID,
        dst_vfid: VFolderID,
    ) -> None:
        """
        Create a new vfolder on the same volume and copy all contents of the source
        vfolder into it, preserving file permissions and timestamps.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_vfolder_mount(self, vfid: VFolderID, subpath: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    async def put_metadata(self, vfid: VFolderID, payload: bytes) -> None:
        pass

    @abstractmethod
    async def get_metadata(self, vfid: VFolderID) -> bytes:
        pass

    @abstractmethod
    async def get_performance_metric(self) -> FSPerfMetric:
        pass

    @abstractmethod
    async def get_fs_usage(self) -> CapacityUsage:
        pass

    @abstractmethod
    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = _CURRENT_DIR,
    ) -> TreeUsage:
        pass

    @abstractmethod
    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        pass

    # ------ vfolder operations -------

    @abstractmethod
    def scandir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        pass

    @abstractmethod
    async def mkdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def rmdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def move_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def move_tree(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def copy_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def prepare_upload(self, vfid: VFolderID) -> str:
        """
        Prepare an upload session by creating a dedicated temporary directory.
        Returns a unique session identifier.
        """
        pass

    @abstractmethod
    async def add_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        payload: AsyncIterator[bytes],
    ) -> None:
        pass

    @abstractmethod
    def read_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        chunk_size: int = 0,
    ) -> AsyncIterator[bytes]:
        pass

    @abstractmethod
    async def delete_files(
        self,
        vfid: VFolderID,
        relpaths: Sequence[PurePosixPath],
        *,
        recursive: bool = False,
    ) -> None:
        pass

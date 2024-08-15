from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    AsyncIterator,
    ClassVar,
    Final,
    FrozenSet,
    Mapping,
    Optional,
    Sequence,
    final,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID

from .exception import InvalidSubpathError, VFolderNotFoundError
from .types import (
    CapacityUsage,
    DirEntry,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    TreeUsage,
    VFolderID,
)

# Available capabilities of a volume implementation
CAP_VFOLDER: Final = "vfolder"  # ability to create vfolder
CAP_METRIC: Final = "metric"  # ability to report disk related metrics
CAP_QUOTA: Final = "quota"  # ability to manage quota limits
CAP_FAST_FS_SIZE: Final = "fast-fs-size"  # ability to scan filesystem size fast (e.g. by API)
CAP_FAST_SCAN: Final = "fast-scan"  # ability to scan number of files in vFolder fast (e.g. by API)
CAP_FAST_SIZE: Final = "fast-size"  # ability to scan vFolder size fast (e.g. by API)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractQuotaModel(metaclass=ABCMeta):
    @abstractmethod
    def mangle_qspath(self, ref: VFolderID | QuotaScopeID | str | None) -> Path:
        raise NotImplementedError

    @abstractmethod
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
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
    ) -> Optional[QuotaUsage]:
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


class AbstractVolume(metaclass=ABCMeta):
    quota_model: AbstractQuotaModel
    fsop_model: AbstractFSOpModel
    name: ClassVar[str] = "undefined"

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispathcer: EventDispatcher,
        event_producer: EventProducer,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.config = options or {}
        self.etcd = etcd
        self.event_dispathcer = event_dispathcer
        self.event_producer = event_producer

    async def init(self) -> None:
        self.fsop_model = await self.create_fsop_model()
        self.quota_model = await self.create_quota_model()

    async def shutdown(self) -> None:
        pass

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
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> Path:
        vfpath = self.mangle_vfpath(vfid).resolve()
        if not (vfpath.exists() and vfpath.is_dir()):
            raise VFolderNotFoundError(vfid)
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
    async def get_capabilities(self) -> FrozenSet[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_hwinfo(self) -> HardwareMetadata:
        raise NotImplementedError

    @abstractmethod
    async def create_vfolder(
        self,
        vfid: VFolderID,
        exist_ok=False,
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
        relpath: PurePosixPath = PurePosixPath("."),
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

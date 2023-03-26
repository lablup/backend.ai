from __future__ import annotations

from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePath, PurePosixPath
from typing import Any, AsyncIterator, Final, FrozenSet, Mapping, Optional, Sequence

from ai.backend.common.types import BinarySize, HardwareMetadata

from .exception import InvalidSubpathError, VFolderNotFoundError
from .types import (
    DirEntry,
    FSPerfMetric,
    FSUsage,
    QuotaOption,
    VFolderCreationOptions,
    VFolderID,
    VFolderUsage,
)

# Available capabilities of a volume implementation
CAP_VFOLDER: Final = "vfolder"  # ability to create vfolder
CAP_VFHOST_QUOTA: Final = "vfhost-quota"  # ability to set quota per vFolder host
CAP_METRIC: Final = "metric"  # ability to report disk related metrics
CAP_QUOTA: Final = "quota"  # ability to set quota per vFolder
CAP_FAST_SCAN: Final = "fast-scan"  # ability to scan number of files in vFolder fast (e.g. by API)
CAP_FAST_SIZE: Final = "fast-size"  # ability to scan vFolder size fast (e.g. by API)


class AbstractVolume(metaclass=ABCMeta):
    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        fsprefix: Optional[PurePath] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.fsprefix = fsprefix or PurePath(".")
        self.config = options or {}

    async def init(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def mangle_vfpath(self, vfid: VFolderID) -> Path:
        folder_id_hex = vfid.folder_id.hex
        prefix1 = folder_id_hex[0:2]
        prefix2 = folder_id_hex[2:4]
        rest = folder_id_hex[4:]
        return Path(self.mount_path, vfid.quota_scope_id, prefix1, prefix2, rest)

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
    async def create_quota_scope(
        self,
        quota_scope_id: str,
        options: Optional[QuotaOption] = None,
    ) -> None:
        """
        Creates a new quota scope.

        Raises `AlreadyExists` error if there is the quota scope with the same name.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_quota_scope(
        self,
        quota_scope_id: str,
    ) -> tuple[QuotaOption, VFolderUsage]:
        """
        Get the information about the given quota scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_quota_scope(
        self,
        quota_scope_id: str,
        options: Optional[QuotaOption] = None,
    ) -> QuotaOption:
        """
        Update the quota option of the given quota scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_quota_scope(
        self,
        quota_scope_id: str,
    ) -> None:
        """
        Deletes the given quota scope.

        Raises `NotEmpty` error if there are one or more vfolders inside the quota scope.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_vfolder(
        self,
        vfid: VFolderID,
        options: VFolderCreationOptions = None,
        *,
        exist_ok: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_vfolder(self, vfid: VFolderID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clone_vfolder(
        self,
        src_vfid: VFolderID,
        dst_volume: AbstractVolume,
        dst_vfid: VFolderID,
        options: VFolderCreationOptions = None,
    ) -> None:
        """
        Create a new vfolder on the destination volume with
        ``exist_ok=True`` option and copy all contents of the source
        vfolder into it, preserving file permissions and timestamps.
        """
        raise NotImplementedError

    @abstractmethod
    async def copy_tree(
        self,
        src_vfpath: Path,
        dst_vfpath: Path,
    ) -> None:
        """
        The actual backend-specific implementation of copying
        files from a directory to another in an efficient way.
        The source and destination are in the same filesystem namespace
        but they may be on different physical media.
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
    async def get_quota(self, vfid: VFolderID) -> BinarySize:
        """
        Gets the currently configured quota size of the given folder.

        .. versionchanged:: 23.03

           Use the quota scopes intead of per-folder quota.
           As of 23.03, this return the quota limit of the quota scope where the given vfolder
           belongs to.
        """
        pass

    @abstractmethod
    async def set_quota(self, vfid: VFolderID, size_bytes: BinarySize) -> None:
        """
        Sets the quota size of the given folder.

        .. versionremoved:: 23.03

           Use the quota scopes intead of per-folder quota.
           As of 23.03, this becomes a no-op.
        """
        pass

    @abstractmethod
    async def get_fs_usage(self) -> FSUsage:
        pass

    @abstractmethod
    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> VFolderUsage:
        pass

    @abstractmethod
    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        pass

    # ------ vfolder operations -------

    @abstractmethod
    def scandir(self, vfid: VFolderID, relpath: PurePosixPath) -> AsyncIterator[DirEntry]:
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
        recursive: bool = False,
    ) -> None:
        pass

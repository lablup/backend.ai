from __future__ import annotations

from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePath, PurePosixPath
from typing import Any, AsyncIterator, Final, FrozenSet, Mapping, Sequence
from uuid import UUID

from ai.backend.common.types import BinarySize, HardwareMetadata

from .exception import InvalidSubpathError, VFolderNotFoundError
from .types import DirEntry, FSPerfMetric, FSUsage, VFolderCreationOptions, VFolderUsage

# Available capabilities of a volume implementation
CAP_VFOLDER: Final = "vfolder"
CAP_VFHOST_QUOTA: Final = "vfhost-quota"
CAP_METRIC: Final = "metric"
CAP_QUOTA: Final = "quota"
CAP_FAST_SCAN: Final = "fast-scan"


class AbstractVolume(metaclass=ABCMeta):
    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        fsprefix: PurePath = None,
        options: Mapping[str, Any] = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.fsprefix = fsprefix or PurePath(".")
        self.config = options or {}

    async def init(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def mangle_vfpath(self, vfid: UUID) -> Path:
        prefix1 = vfid.hex[0:2]
        prefix2 = vfid.hex[2:4]
        rest = vfid.hex[4:]
        return Path(self.mount_path, prefix1, prefix2, rest)

    def sanitize_vfpath(
        self,
        vfid: UUID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> Path:
        vfpath = self.mangle_vfpath(vfid).resolve()
        if not (vfpath.exists() and vfpath.is_dir()):
            raise VFolderNotFoundError(vfid)
        target_path = (vfpath / relpath).resolve()
        if not target_path.is_relative_to(vfpath):
            raise InvalidSubpathError(vfid, relpath)
        return target_path

    def strip_vfpath(self, vfid: UUID, target_path: Path) -> PurePosixPath:
        vfpath = self.mangle_vfpath(vfid).resolve()
        return PurePosixPath(target_path.relative_to(vfpath))

    # ------ volume operations -------

    @abstractmethod
    async def get_capabilities(self) -> FrozenSet[str]:
        pass

    @abstractmethod
    async def get_hwinfo(self) -> HardwareMetadata:
        pass

    @abstractmethod
    async def create_vfolder(
        self,
        vfid: UUID,
        options: VFolderCreationOptions = None,
        *,
        exist_ok: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def delete_vfolder(self, vfid: UUID) -> None:
        pass

    @abstractmethod
    async def clone_vfolder(
        self,
        src_vfid: UUID,
        dst_volume: AbstractVolume,
        dst_vfid: UUID,
        options: VFolderCreationOptions = None,
    ) -> None:
        """
        Create a new vfolder on the destination volume with
        ``exist_ok=True`` option and copy all contents of the source
        vfolder into it, preserving file permissions and timestamps.
        """
        pass

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
        pass

    @abstractmethod
    async def get_vfolder_mount(self, vfid: UUID, subpath: str) -> Path:
        pass

    @abstractmethod
    async def put_metadata(self, vfid: UUID, payload: bytes) -> None:
        pass

    @abstractmethod
    async def get_metadata(self, vfid: UUID) -> bytes:
        pass

    @abstractmethod
    async def get_performance_metric(self) -> FSPerfMetric:
        pass

    @abstractmethod
    async def get_quota(self, vfid: UUID) -> BinarySize:
        pass

    @abstractmethod
    async def set_quota(self, vfid: UUID, size_bytes: BinarySize) -> None:
        pass

    @abstractmethod
    async def get_fs_usage(self) -> FSUsage:
        pass

    @abstractmethod
    async def get_usage(
        self,
        vfid: UUID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> VFolderUsage:
        pass

    @abstractmethod
    async def get_used_bytes(self, vfid: UUID) -> BinarySize:
        pass

    # ------ vfolder operations -------

    @abstractmethod
    def scandir(self, vfid: UUID, relpath: PurePosixPath) -> AsyncIterator[DirEntry]:
        pass

    @abstractmethod
    async def mkdir(
        self,
        vfid: UUID,
        relpath: PurePosixPath,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def rmdir(
        self,
        vfid: UUID,
        relpath: PurePosixPath,
        *,
        recursive: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def move_file(
        self,
        vfid: UUID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def move_tree(
        self,
        vfid: UUID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def copy_file(
        self,
        vfid: UUID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @abstractmethod
    async def prepare_upload(self, vfid: UUID) -> str:
        """
        Prepare an upload session by creating a dedicated temporary directory.
        Returns a unique session identifier.
        """
        pass

    @abstractmethod
    async def add_file(
        self,
        vfid: UUID,
        relpath: PurePosixPath,
        payload: AsyncIterator[bytes],
    ) -> None:
        pass

    @abstractmethod
    def read_file(
        self,
        vfid: UUID,
        relpath: PurePosixPath,
        *,
        chunk_size: int = 0,
    ) -> AsyncIterator[bytes]:
        pass

    @abstractmethod
    async def delete_files(
        self,
        vfid: UUID,
        relpaths: Sequence[PurePosixPath],
        recursive: bool = False,
    ) -> None:
        pass

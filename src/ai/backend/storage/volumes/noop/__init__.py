from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, override

from ai.backend.common.defs import DEFAULT_VFOLDER_PERMISSION_MODE, NOOP_STORAGE_BACKEND_TYPE
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID
from ai.backend.storage.types import (
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    Stat,
    TreeUsage,
    VFolderID,
    VolumeInfo,
)
from ai.backend.storage.volumes.abc import (
    _CURRENT_DIR,
    AbstractFSOpModel,
    AbstractQuotaModel,
    AbstractVolume,
)


async def _return_empty_dir_entry() -> AsyncIterator[DirEntry]:
    yield DirEntry(
        "", Path(), DirEntryType.FILE, Stat(0, "", 0, datetime.now(UTC), datetime.now(UTC)), ""
    )


class NoopQuotaModel(AbstractQuotaModel):
    def __init__(self) -> None:
        pass

    @override
    def mangle_qspath(self, ref: VFolderID | QuotaScopeID | str | None) -> Path:
        return Path()

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        pass

    @override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        pass

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        pass

    @override
    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass


class NoopFSOpModel(AbstractFSOpModel):
    def __init__(self) -> None:
        return

    @override
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        pass

    @override
    async def move_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        pass

    @override
    async def delete_tree(
        self,
        path: Path,
    ) -> None:
        pass

    @override
    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        return _return_empty_dir_entry()

    @override
    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        return TreeUsage(0, 0)

    @override
    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        return BinarySize(0)


class NoopVolume(AbstractVolume):
    name = NOOP_STORAGE_BACKEND_TYPE

    @override
    def info(self) -> VolumeInfo:
        return VolumeInfo(
            backend=NOOP_STORAGE_BACKEND_TYPE,
            path=self.mount_path,
            fsprefix=None,
            options=None,
        )

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return NoopQuotaModel()

    @override
    async def create_fsop_model(self) -> AbstractFSOpModel:
        return NoopFSOpModel()

    # ------ volume operations -------

    @override
    async def get_capabilities(self) -> frozenset[str]:
        return frozenset()

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {},
        }

    @override
    async def create_vfolder(
        self,
        vfid: VFolderID,
        exist_ok: bool = False,
        mode: int = DEFAULT_VFOLDER_PERMISSION_MODE,
    ) -> None:
        return None

    @override
    async def delete_vfolder(self, vfid: VFolderID) -> None:
        return None

    @override
    async def clone_vfolder(
        self,
        src_vfid: VFolderID,
        dst_vfid: VFolderID,
    ) -> None:
        return None

    @override
    async def get_vfolder_mount(self, vfid: VFolderID, subpath: str) -> Path:
        return Path()

    @override
    async def put_metadata(self, vfid: VFolderID, payload: bytes) -> None:
        pass

    @override
    async def get_metadata(self, vfid: VFolderID) -> bytes:
        return b""

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        return FSPerfMetric(0, 0, 0, 0, 0.0, 0.0)

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        return CapacityUsage(0, 0)

    @override
    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = _CURRENT_DIR,
    ) -> TreeUsage:
        return TreeUsage(0, 0)

    @override
    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        return BinarySize(0)

    # ------ vfolder operations -------

    @override
    def scandir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        return _return_empty_dir_entry()

    @override
    async def mkdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        pass

    @override
    async def rmdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = False,
    ) -> None:
        pass

    @override
    async def move_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @override
    async def move_tree(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @override
    async def copy_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    @override
    async def prepare_upload(self, vfid: VFolderID) -> str:
        return ""

    @override
    async def add_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        payload: AsyncIterator[bytes],
    ) -> None:
        pass

    @override
    def read_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        chunk_size: int = 0,
    ) -> AsyncIterator[bytes]:
        async def _noop() -> AsyncIterator[bytes]:
            yield b""

        return _noop()

    @override
    async def delete_files(
        self,
        vfid: VFolderID,
        relpaths: Sequence[PurePosixPath],
        *,
        recursive: bool = False,
    ) -> None:
        pass


def init_noop_volume(
    etcd: AsyncEtcd,
    event_dispatcher: EventDispatcher,
    event_producer: EventProducer,
) -> NoopVolume:
    return NoopVolume(
        {},
        Path(),
        etcd=etcd,
        event_dispatcher=event_dispatcher,
        event_producer=event_producer,
        watcher=None,
        options=None,
    )

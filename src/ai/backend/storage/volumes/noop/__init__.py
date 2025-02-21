from collections.abc import Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, AsyncIterator, Optional

from ai.backend.common.defs import DEFAULT_VFOLDER_PERMISSION_MODE, NOOP_STORAGE_BACKEND_TYPE
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID

from ...types import (
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    Stat,
    TreeUsage,
    VFolderID,
)
from ..abc import AbstractFSOpModel, AbstractQuotaModel, AbstractVolume


async def _return_empty_dir_entry() -> AsyncIterator[DirEntry]:
    yield DirEntry(
        "", Path(), DirEntryType.FILE, Stat(0, "", 0, datetime.now(), datetime.now()), ""
    )


class NoopQuotaModel(AbstractQuotaModel):
    def __init__(self) -> None:
        pass

    def mangle_qspath(self, ref: VFolderID | QuotaScopeID | str | None) -> Path:
        return Path()

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        pass

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        pass

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        pass

    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass


class NoopFSOpModel(AbstractFSOpModel):
    def __init__(self) -> None:
        return

    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        pass

    async def move_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        pass

    async def delete_tree(
        self,
        path: Path,
    ) -> None:
        pass

    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        return _return_empty_dir_entry()

    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        return TreeUsage(0, 0)

    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        return BinarySize(0)


class NoopVolume(AbstractVolume):
    name = NOOP_STORAGE_BACKEND_TYPE

    async def create_quota_model(self) -> AbstractQuotaModel:
        return NoopQuotaModel()

    async def create_fsop_model(self) -> AbstractFSOpModel:
        return NoopFSOpModel()

    # ------ volume operations -------

    async def get_capabilities(self) -> frozenset[str]:
        return frozenset()

    async def get_hwinfo(self) -> HardwareMetadata:
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {},
        }

    async def create_vfolder(
        self,
        vfid: VFolderID,
        exist_ok: bool = False,
        mode: int = DEFAULT_VFOLDER_PERMISSION_MODE,
    ) -> None:
        return None

    async def delete_vfolder(self, vfid: VFolderID) -> None:
        return None

    async def clone_vfolder(
        self,
        src_vfid: VFolderID,
        dst_vfid: VFolderID,
    ) -> None:
        return None

    async def get_vfolder_mount(self, vfid: VFolderID, subpath: str) -> Path:
        return Path()

    async def put_metadata(self, vfid: VFolderID, payload: bytes) -> None:
        pass

    async def get_metadata(self, vfid: VFolderID) -> bytes:
        return b""

    async def get_performance_metric(self) -> FSPerfMetric:
        return FSPerfMetric(0, 0, 0, 0, 0.0, 0.0)

    async def get_fs_usage(self) -> CapacityUsage:
        return CapacityUsage(0, 0)

    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> TreeUsage:
        return TreeUsage(0, 0)

    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        return BinarySize(0)

    # ------ vfolder operations -------

    def scandir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        return _return_empty_dir_entry()

    async def mkdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        pass

    async def rmdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = False,
    ) -> None:
        pass

    async def move_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    async def move_tree(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    async def copy_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        pass

    async def prepare_upload(self, vfid: VFolderID) -> str:
        return ""

    async def add_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        payload: AsyncIterator[bytes],
    ) -> None:
        pass

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

from __future__ import annotations

import asyncio
import errno
import functools
import logging
import os
import secrets
import shutil
import time
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any, AsyncIterator, FrozenSet, Optional, Sequence, Union, final

import aiofiles.os
import janus
import trafaret as t

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID

from ..abc import CAP_VFOLDER, AbstractFSOpModel, AbstractQuotaModel, AbstractVolume
from ..exception import (
    ExecutionError,
    InvalidAPIParameters,
    InvalidQuotaScopeError,
    NotEmptyError,
    QuotaScopeNotFoundError,
)
from ..subproc import run
from ..types import (
    SENTINEL,
    CapacityUsage,
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    QuotaConfig,
    QuotaUsage,
    Sentinel,
    Stat,
    TreeUsage,
    VFolderID,
)
from ..utils import fstime2datetime

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class BaseQuotaModel(AbstractQuotaModel):
    """
    This quota model just creates the first-level volume directories
    to split vfolders into per-user/per-project namespaces, without
    imposing any actual quota limits.
    """

    def __init__(self, mount_path: Path) -> None:
        self.mount_path = mount_path

    def mangle_qspath(self, ref: VFolderID | QuotaScopeID | str | None) -> Path:
        try:
            match ref:
                case VFolderID():
                    if ref.quota_scope_id is None:
                        return self.mount_path  # for legacy vfolder paths during migration
                    return Path(self.mount_path, ref.quota_scope_id.pathname)
                case QuotaScopeID():
                    return Path(self.mount_path, ref.pathname)
                case str():
                    typed_scope_id = QuotaScopeID.parse(ref)
                    return Path(self.mount_path, typed_scope_id.pathname)
                case None:
                    return self.mount_path  # for legacy vfolder paths during migration
                case _:
                    raise InvalidQuotaScopeError(
                        f"Invalid value format for quota scope ID: {ref!r}"
                    )
        except t.DataError:
            raise InvalidQuotaScopeError(f"Invalid value format for quota scope ID: {ref!r}")

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: qspath.mkdir(0o755, parents=True, exist_ok=False),
        )

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        if not self.mangle_qspath(quota_scope_id).exists():
            return None

        return QuotaUsage(-1, -1)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        # This is a no-op.
        pass

    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        # This is a no-op.
        pass

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: shutil.rmtree(qspath),
        )


class SetGIDQuotaModel(BaseQuotaModel):
    """
    This quota model uses the Linux's vanilla gid-based quota scheme
    with setgid on the first-level namespace directories for each user
    or each project.
    """

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: qspath.mkdir(0o755, parents=True, exist_ok=False),
        )
        # TODO: setgid impl.

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        if not self.mangle_qspath(quota_scope_id).exists():
            return None
        # TODO: setgid impl.
        return QuotaUsage(-1, -1)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig,
    ) -> None:
        # TODO: setgid impl.
        raise NotImplementedError

    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        # TODO: setgid impl.
        raise NotImplementedError

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: shutil.rmtree(qspath),
        )
        # TODO: setgid impl.


class BaseFSOpModel(AbstractFSOpModel):
    def __init__(self, mount_path: Path, scandir_limit: int) -> None:
        self.mount_path = mount_path
        self.scandir_limit = scandir_limit

    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            functools.partial(
                shutil.copytree,
                src_path,
                dst_path,
                dirs_exist_ok=True,
            ),
        )

    async def move_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: shutil.move(str(src_path), str(dst_path)),
        )

    async def delete_tree(
        self,
        path: Path,
    ) -> None:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, functools.partial(shutil.rmtree, path))
        except FileNotFoundError:
            pass

    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        q: janus.Queue[Sentinel | DirEntry] = janus.Queue()
        loop = asyncio.get_running_loop()

        def _scandir(path: Path, q: janus._SyncQueueProxy[Sentinel | DirEntry]) -> None:
            count = 0
            limit = self.scandir_limit
            next_paths: deque[Path] = deque()
            next_paths.append(path)
            while next_paths:
                next_path = next_paths.popleft()
                with os.scandir(next_path) as scanner:
                    for entry in scanner:
                        if limit > 0 and count == limit:
                            break
                        symlink_target = ""
                        entry_type = DirEntryType.FILE
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                entry_type = DirEntryType.DIRECTORY
                            if entry.is_symlink():
                                entry_type = DirEntryType.SYMLINK
                                try:
                                    symlink_dst = Path(entry).resolve()
                                    symlink_dst = symlink_dst.relative_to(path)
                                except (ValueError, RuntimeError):
                                    # ValueError and ELOOP
                                    pass
                                else:
                                    symlink_target = os.fsdecode(symlink_dst)
                            entry_stat = entry.stat(follow_symlinks=False)
                        except (FileNotFoundError, PermissionError):
                            # the filesystem may be changed during scan
                            continue
                        item = DirEntry(
                            name=entry.name,
                            path=Path(entry.path).relative_to(path),
                            type=entry_type,
                            stat=Stat(
                                size=entry_stat.st_size,
                                owner=str(entry_stat.st_uid),
                                mode=entry_stat.st_mode,
                                modified=fstime2datetime(entry_stat.st_mtime),
                                created=fstime2datetime(entry_stat.st_ctime),
                            ),
                            symlink_target=symlink_target,
                        )
                        q.put(item)
                        if recursive and entry.is_dir() and not entry.is_symlink():
                            next_paths.append(Path(entry.path))
                        count += 1

        async def _scan_task(q: janus.Queue[Sentinel | DirEntry]) -> None:
            try:
                await loop.run_in_executor(None, _scandir, path, q.sync_q)
            finally:
                await q.async_q.put(SENTINEL)

        async def _aiter() -> AsyncIterator[DirEntry]:
            scan_task = asyncio.create_task(_scan_task(q))
            await asyncio.sleep(0)
            try:
                while True:
                    item = await q.async_q.get()
                    try:
                        if item is SENTINEL:
                            break
                        yield item
                    finally:
                        q.async_q.task_done()
            finally:
                await scan_task
                q.close()
                await q.wait_closed()

        return _aiter()

    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        total_size = 0
        total_count = 0
        start_time = time.monotonic()
        _timeout = 30

        def _calc_usage(path: Path) -> None:
            nonlocal total_size, total_count
            next_paths: deque[Path] = deque()
            next_paths.append(path)
            while next_paths:
                next_path = next_paths.popleft()
                with os.scandir(next_path) as scanner:  # type: ignore
                    for entry in scanner:
                        try:
                            stat = entry.stat(follow_symlinks=False)
                        except (FileNotFoundError, PermissionError):
                            # the filesystem may be changed during scan
                            continue
                        total_size += stat.st_size
                        total_count += 1
                        if entry.is_dir() and not entry.is_symlink():
                            next_paths.append(Path(entry.path))
                        if total_count % 1000 == 0:
                            # Cancel if this I/O operation takes too much time.
                            if time.monotonic() - start_time > _timeout:
                                raise TimeoutError

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, _calc_usage, path)
        except TimeoutError:
            # -1 indicates "too many"
            total_size = -1
            total_count = -1
        return TreeUsage(file_count=total_count, used_bytes=total_size)

    async def scan_tree_size(
        self,
        path: Path,
    ) -> BinarySize:
        info = await run(["du", "-hs", path])
        used_bytes, _ = info.split()
        return BinarySize.finite_from_str(used_bytes)


class BaseVolume(AbstractVolume):
    name = "vfs"

    async def create_quota_model(self) -> AbstractQuotaModel:
        return BaseQuotaModel(self.mount_path)

    async def create_fsop_model(self) -> AbstractFSOpModel:
        return BaseFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER])

    async def get_hwinfo(self) -> HardwareMetadata:
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {},
        }

    @final
    async def create_vfolder(
        self,
        vfid: VFolderID,
        exist_ok=False,
    ) -> None:
        qspath = self.quota_model.mangle_qspath(vfid)
        if not qspath.exists():
            raise QuotaScopeNotFoundError
        vfpath = self.mangle_vfpath(vfid)
        await aiofiles.os.makedirs(vfpath, 0o755, exist_ok=exist_ok)

    @final
    async def delete_vfolder(self, vfid: VFolderID) -> None:
        vfpath = self.mangle_vfpath(vfid)
        await self.fsop_model.delete_tree(vfpath)
        for p in [vfpath, vfpath.parent, vfpath.parent.parent]:
            try:
                await aiofiles.os.rmdir(p)
            except FileNotFoundError:
                pass
            except OSError as e:
                match e.errno:
                    case errno.ENOTEMPTY:
                        pass
                    case _:
                        raise

    @final
    async def clone_vfolder(
        self,
        src_vfid: VFolderID,
        dst_vfid: VFolderID,
    ) -> None:
        # check if there is enough space in the destination
        fs_usage = await self.get_fs_usage()
        vfolder_usage = await self.get_usage(src_vfid)
        if vfolder_usage.used_bytes > fs_usage.capacity_bytes - fs_usage.used_bytes:
            raise ExecutionError("Not enough space available for clone.")

        # create the target vfolder
        src_vfpath = self.mangle_vfpath(src_vfid)
        await self.create_vfolder(dst_vfid)
        dst_vfpath = self.mangle_vfpath(dst_vfid)

        # perform the file-tree copy
        try:
            await self.fsop_model.copy_tree(src_vfpath, dst_vfpath)
        except Exception:
            await self.delete_vfolder(dst_vfid)
            log.exception("clone_vfolder: error during copy_tree()")
            raise ExecutionError("Copying files from source directories failed.")

    @final
    async def get_vfolder_mount(self, vfid: VFolderID, subpath: str) -> Path:
        self.sanitize_vfpath(vfid, PurePosixPath(subpath))
        return self.mangle_vfpath(vfid).resolve()

    async def put_metadata(self, vfid: VFolderID, payload: bytes) -> None:
        vfpath = self.mangle_vfpath(vfid)
        metadata_path = vfpath / "metadata.json"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, metadata_path.write_bytes, payload)

    async def get_metadata(self, vfid: VFolderID) -> bytes:
        vfpath = self.mangle_vfpath(vfid)
        metadata_path = vfpath / "metadata.json"
        loop = asyncio.get_running_loop()
        try:
            stat = await loop.run_in_executor(None, metadata_path.stat)
            if stat.st_size > 10 * (2**20):
                raise RuntimeError("Too large metadata (more than 10 MiB)")
            data = await loop.run_in_executor(None, metadata_path.read_bytes)
            return data
        except FileNotFoundError:
            return b""
        # Other IO errors should be bubbled up.

    async def get_performance_metric(self) -> FSPerfMetric:
        raise NotImplementedError

    async def get_fs_usage(self) -> CapacityUsage:
        loop = asyncio.get_running_loop()
        stat = await loop.run_in_executor(None, os.statvfs, self.mount_path)
        return CapacityUsage(
            capacity_bytes=BinarySize(stat.f_frsize * stat.f_blocks),
            used_bytes=BinarySize(stat.f_frsize * (stat.f_blocks - stat.f_bavail)),
        )

    @final
    async def get_usage(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> TreeUsage:
        target_path = self.sanitize_vfpath(vfid, relpath)
        return await self.fsop_model.scan_tree_usage(target_path)

    @final
    async def get_used_bytes(self, vfid: VFolderID) -> BinarySize:
        vfpath = self.mangle_vfpath(vfid)
        return await self.fsop_model.scan_tree_size(vfpath)

    # ------ vfolder internal operations -------

    @final
    def scandir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        target_path = self.sanitize_vfpath(vfid, relpath)
        return self.fsop_model.scan_tree(target_path, recursive=recursive)

    async def mkdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        target_path = self.sanitize_vfpath(vfid, relpath)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: target_path.mkdir(0o755, parents=parents, exist_ok=exist_ok),
        )

    async def rmdir(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        recursive: bool = False,
    ) -> None:
        target_path = self.sanitize_vfpath(vfid, relpath)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, target_path.rmdir)

    async def move_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        src_path = self.sanitize_vfpath(vfid, src)
        dst_path = self.sanitize_vfpath(vfid, dst)
        await self.fsop_model.move_tree(src_path, dst_path)

    async def move_tree(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        src_path = self.sanitize_vfpath(vfid, src)
        if not src_path.is_dir():
            raise InvalidAPIParameters(
                msg=f"source path {str(src_path)} is not a directory",
            )
        dst_path = self.sanitize_vfpath(vfid, dst)
        await self.fsop_model.move_tree(src_path, dst_path)

    async def copy_file(
        self,
        vfid: VFolderID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        src_path = self.sanitize_vfpath(vfid, src)
        if not src_path.is_file():
            raise InvalidAPIParameters(msg=f"source path {str(src_path)} is not a file")
        dst_path = self.sanitize_vfpath(vfid, dst)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: dst_path.parent.mkdir(parents=True, exist_ok=True),
        )
        await self.fsop_model.copy_tree(src_path, dst_path)

    async def prepare_upload(self, vfid: VFolderID) -> str:
        vfpath = self.mangle_vfpath(vfid)
        session_id = secrets.token_hex(16)

        def _create_target():
            upload_base_path = vfpath / ".upload"
            upload_base_path.mkdir(exist_ok=True)
            upload_target_path = upload_base_path / session_id
            upload_target_path.touch()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _create_target)
        return session_id

    async def add_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        payload: AsyncIterator[bytes],
    ) -> None:
        target_path = self.sanitize_vfpath(vfid, relpath)
        q: janus.Queue[bytes] = janus.Queue()

        def _write(q: janus._SyncQueueProxy[bytes]) -> None:
            with open(target_path, "wb") as f:
                while True:
                    buf = q.get()
                    try:
                        if not buf:
                            return
                        f.write(buf)
                    finally:
                        q.task_done()

        loop = asyncio.get_running_loop()
        write_task: asyncio.Task = asyncio.create_task(
            loop.run_in_executor(None, _write, q.sync_q),  # type: ignore
        )
        try:
            async for buf in payload:
                await q.async_q.put(buf)
            await q.async_q.put(b"")
            await q.async_q.join()
        finally:
            await write_task

    def read_file(
        self,
        vfid: VFolderID,
        relpath: PurePosixPath,
        *,
        chunk_size: int = 0,
    ) -> AsyncIterator[bytes]:
        target_path = self.sanitize_vfpath(vfid, relpath)
        q: janus.Queue[Union[bytes, Exception]] = janus.Queue()
        loop = asyncio.get_running_loop()

        def _read(
            q: janus._SyncQueueProxy[Union[bytes, Exception]],
            chunk_size: int,
        ) -> None:
            try:
                with open(target_path, "rb") as f:
                    while True:
                        buf = f.read(chunk_size)
                        if not buf:
                            return
                        q.put(buf)
            except Exception as e:
                q.put(e)
            finally:
                q.put(b"")

        async def _aiter() -> AsyncIterator[bytes]:
            nonlocal chunk_size
            if chunk_size == 0:
                # get the preferred io block size
                _vfs_stat = await loop.run_in_executor(
                    None,
                    os.statvfs,
                    self.mount_path,
                )
                chunk_size = _vfs_stat.f_bsize
            read_fut = loop.run_in_executor(None, _read, q.sync_q, chunk_size)
            await asyncio.sleep(0)
            try:
                while True:
                    buf = await q.async_q.get()
                    if isinstance(buf, Exception):
                        raise buf
                    yield buf
                    q.async_q.task_done()
                    if not buf:
                        return
            finally:
                await read_fut

        return _aiter()

    async def delete_files(
        self,
        vfid: VFolderID,
        relpaths: Sequence[PurePosixPath],
        *,
        recursive: bool = False,
    ) -> None:
        target_paths = [self.sanitize_vfpath(vfid, p) for p in relpaths]
        for p in target_paths:
            if p.is_dir() and recursive:
                await self.fsop_model.delete_tree(p)
            else:
                await aiofiles.os.remove(p)

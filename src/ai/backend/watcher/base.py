from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Generic,
    Mapping,
    TypeVar,
    cast,
)

from async_timeout import timeout

from ai.backend.common.lock import FileLock
from ai.backend.common.types import JSONSerializableMixin
from ai.backend.common.utils import mount as _mount
from ai.backend.common.utils import umount as _umount

from .defs import WatcherName
from .types import ProcResult

if TYPE_CHECKING:
    from .context import RootContext


DEFAULT_FILE_IO_TIMEOUT: Final = 60
DEFAULT_POLLING_INTERVAL: Final = 30


class MountErrorHandler(metaclass=ABCMeta):
    @abstractmethod
    async def call(self, path: str, reason: str) -> None:
        pass


async def _run_cmd(cmd: list[str]) -> ProcResult:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    raw_out, raw_err = await proc.communicate()
    out, err = raw_out.decode("utf8"), raw_err.decode("utf8")
    if err:
        result = ProcResult(False, err)
    else:
        result = ProcResult(True, out)
    return result


async def _run_cmd_timeout(cmd: list[str], timeout_sec: float) -> ProcResult:
    with timeout(timeout_sec):
        return await _run_cmd(cmd)


class BaseWatcherConfig(JSONSerializableMixin):
    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> BaseWatcherConfig:
        return cls(**cls.as_trafaret().check(obj))


WatcherConfigType = TypeVar("WatcherConfigType", bound=BaseWatcherConfig)


class BaseWatcher(Generic[WatcherConfigType], metaclass=ABCMeta):
    ctx: RootContext
    config: WatcherConfigType
    name: ClassVar[WatcherName] = WatcherName("base")

    def __init__(
        self, ctx: RootContext, config_cls: type[WatcherConfigType], obj: Mapping[str, Any]
    ) -> None:
        self.ctx = ctx
        self.config = cast(WatcherConfigType, config_cls.from_json(obj))

    @abstractmethod
    async def init(self) -> None:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    async def run_cmd(
        self,
        cmd: list[str],
        *,
        timeout: float | None = None,
    ) -> ProcResult:
        if timeout is not None:
            return await _run_cmd_timeout(cmd, timeout)
        else:
            return await _run_cmd(cmd)

    async def mount(
        self,
        mount_path: str,
        fs_location: str,
        fs_type: str = "nfs",
        cmd_options: str | None = None,
        edit_fstab: bool = False,
        fstab_path: str | None = None,
    ) -> bool:
        """
        Run mount command through `ai.backend.common.utils.mount()` API
        with `ai.backend.common.lock.FileLock`.

        Return True if mount is successful.
        Return False if the given path is already mounted.
        Raise `ai.backend.common.exception.VolumeMountFailed` if any error occurs during mount.
        """
        _mount_path = Path(mount_path)

        def already_done() -> bool:
            return _mount_path.is_mount()

        if already_done():
            return False
        lock_path = FileLock.get_dir_lock_path(_mount_path)
        async with FileLock(lock_path, remove_when_unlock=True):
            if already_done():
                return False
            await _mount(
                mount_path,
                fs_location,
                fs_type,
                cmd_options,
                edit_fstab,
                fstab_path,
            )
            return True

    async def umount(
        self,
        mount_path: str,
        edit_fstab: bool = False,
        fstab_path: str | None = None,
        rmdir_if_empty: bool = False,
        *,
        timeout_sec: float | None = DEFAULT_FILE_IO_TIMEOUT,
    ) -> bool:
        """
        Run umount command through `ai.backend.common.utils.umount()` API
        with `ai.backend.common.lock.FileLock`.

        Return True if umount is successful.
        Return False if the given path is already umounted.
        Raise `ai.backend.common.exception.VolumeMountFailed` if any error occurs during umount.
        """
        _mount_path = Path(mount_path)

        def already_done() -> bool:
            if _mount_path.is_mount():
                return False
            if rmdir_if_empty and _mount_path.is_dir():
                return False
            return True

        if already_done():
            return False
        lock_path = FileLock.get_dir_lock_path(_mount_path)
        async with FileLock(lock_path, remove_when_unlock=True):
            if already_done():
                return False
            return await _umount(
                mount_path,
                edit_fstab,
                fstab_path,
                rmdir_if_empty,
                timeout_sec=timeout_sec,
            )

    async def poll_check_mount(
        self,
        mount_paths: list[str],
        *,
        interval: float = DEFAULT_POLLING_INTERVAL,
        error_handler: MountErrorHandler,
        return_when_error: bool = False,
    ) -> None:
        while True:
            for path in mount_paths:
                if not Path(path).is_mount():
                    await error_handler.call(path, "unknown")
                    if return_when_error:
                        return
            await asyncio.sleep(interval)

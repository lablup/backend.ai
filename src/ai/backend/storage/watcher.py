from __future__ import annotations

import asyncio
import logging
import os
from abc import ABCMeta, abstractmethod
from typing import Any, ClassVar, Sequence, Type

import attrs

from ai.backend.common import msgpack
from ai.backend.common.events import DoVolumeMountEvent, DoVolumeUnmountEvent
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import QuotaScopeID
from ai.backend.common.utils import mount as _mount
from ai.backend.common.utils import umount as _umount

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


async def cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    cancelled_tasks = []
    for task in asyncio.all_tasks():
        if not task.done() and task is not asyncio.current_task():
            task.cancel()
            cancelled_tasks.append(task)
    await asyncio.gather(*cancelled_tasks, return_exceptions=True)
    for task in cancelled_tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during loop shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


# Using extra_procs
def main_job(
    reader_fd: int,
    writer_fd: int,
    intr_event: Any,
    pidx: int,
    args: Sequence[Any],
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(_main_job(loop, reader_fd, writer_fd))
    # try:
    #     loop.run_until_complete(_main_job(loop, job_rfd))
    # finally:
    #     try:
    #         loop.run_until_complete(cancel_all_tasks(loop))
    #         loop.run_until_complete(loop.shutdown_asyncgens())
    #         try:
    #             loop.run_until_complete(loop.shutdown_default_executor())
    #         except (AttributeError, NotImplementedError):  # for uvloop
    #             pass
    #     finally:
    #         loop.close()
    #         asyncio.set_event_loop(None)


async def _main_job(
    loop: asyncio.AbstractEventLoop,
    reader_fd: int,
    writer_fd: int,
) -> None:
    while True:
        print("Wait for pipe ...", flush=True)
        # with open(job_rfd, "rb") as fp:
        #     data = fp.read()
        #     print(f"{data = }")

        # async with aiofiles.open(job_rfd, mode="rb") as fp:
        #     data = await fp.read()
        #     print(f'{data = }', flush=True)

        # raw_data = await loop.run_in_executor(None, _read)
        raw_data = await WatcherClient.read_pipe(reader_fd)
        print(f"{raw_data = }", flush=True)
        # await WatcherClient.run_pipe_task(raw_data)


class AbstractTask(metaclass=ABCMeta):
    name: ClassVar[str] = "undefined"

    @abstractmethod
    async def run(self) -> None:
        pass

    async def request(self, watcher: WatcherClient) -> None:
        await watcher.write_pipe(self.serialize())

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, values: tuple) -> AbstractTask:
        pass


@attrs.define(slots=True)
class ChownTask(AbstractTask):
    name = "chown"

    directory: str = attrs.field()
    uid: int = attrs.field()
    gid: int = attrs.field()

    async def run(self) -> None:
        os.chown(self.directory, self.uid, self.gid)

    def serialize(self) -> bytes:
        return msgpack.packb(
            (
                self.name,
                self.directory,
                self.uid,
                self.gid,
            )
        )

    @classmethod
    def deserialize(cls, values: tuple) -> ChownTask:
        return ChownTask(
            values[0],
            values[1],
            values[2],
        )


@attrs.define(slots=True)
class MountTask(AbstractTask):
    name = "mount"

    mount_path: str = attrs.field()
    quota_scope_id: QuotaScopeID = attrs.field()

    fs_location: str = attrs.field()
    fs_type: str = attrs.field(default="nfs")
    cmd_options: str | None = attrs.field(default=None)
    scaling_group: str | None = attrs.field(default=None)

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = attrs.field(default=False)
    fstab_path: str = attrs.field(default="/etc/fstab")
    mount_prefix: str | None = attrs.field(default=None)

    async def run(self) -> None:
        await _mount(
            self.mount_path,
            self.fs_location,
            self.fs_type,
            self.cmd_options,
            self.edit_fstab,
            self.fstab_path,
            self.mount_prefix,
        )

    @classmethod
    def from_event(cls, event: DoVolumeMountEvent, mount_prefix: str | None = None) -> MountTask:
        return MountTask(
            event.mount_path,
            event.quota_scope_id,
            event.fs_location,
            event.fs_type,
            event.cmd_options,
            event.scaling_group,
            event.edit_fstab,
            event.fstab_path,
            mount_prefix,
        )

    def serialize(self) -> bytes:
        return msgpack.packb(
            (
                self.name,
                self.mount_path,
                self.quota_scope_id,
                self.fs_location,
                self.fs_type,
                self.cmd_options,
                self.scaling_group,
                self.edit_fstab,
                self.fstab_path,
            )
        )

    @classmethod
    def deserialize(cls, values: tuple) -> MountTask:
        return MountTask(
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
        )


@attrs.define(slots=True)
class UmountTask(AbstractTask):
    name = "umount"

    mount_path: str = attrs.field()
    quota_scope_id: QuotaScopeID = attrs.field()
    scaling_group: str | None = attrs.field(default=None)

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = attrs.field(default=False)
    fstab_path: str | None = attrs.field(default=None)
    mount_prefix: str | None = attrs.field(default=None)

    async def run(self) -> None:
        await _umount(
            self.mount_path,
            edit_fstab=self.edit_fstab,
            fstab_path=self.fstab_path,
        )

    @classmethod
    def from_event(cls, event: DoVolumeUnmountEvent, mount_prefix: str | None = None) -> UmountTask:
        return UmountTask(
            event.mount_path,
            event.quota_scope_id,
            event.scaling_group,
            event.edit_fstab,
            event.fstab_path,
            mount_prefix,
        )

    def serialize(self) -> bytes:
        return msgpack.packb(
            (
                self.name,
                self.mount_path,
                self.quota_scope_id,
                self.scaling_group,
                self.edit_fstab,
                self.fstab_path,
                self.mount_prefix,
            )
        )

    @classmethod
    def deserialize(cls, values: tuple) -> UmountTask:
        return UmountTask(
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
        )


# TaskType = TypeVar("TaskType", bound=AbstractTask)

SERIALIZER_MAP: dict[str, Type[AbstractTask]] = {
    MountTask.name: MountTask,
    UmountTask.name: UmountTask,
    ChownTask.name: ChownTask,
}


def _deserialize(raw_data: bytes) -> AbstractTask:
    values: tuple = msgpack.unpackb(raw_data)
    serializer_name = values[0]
    serializer_cls = SERIALIZER_MAP[serializer_name]
    return serializer_cls.deserialize(values[1:])


class WatcherClient:
    def __init__(
        self,
        reader_fd: int,
        writer_fd: int,
    ) -> None:
        self.reader_fd = reader_fd
        self.writer_fd = writer_fd

        # self.job_queue = job_queue

    # @classmethod
    # async def read_queue(cls, queue: queue.Queue[bytes | Sentinel]) -> bytes | Sentinel:
    #     def _read() -> bytes | Sentinel:
    #         return queue.get()
    #     return await asyncio.get_running_loop().run_in_executor(None, _read)

    # async def write_queue(self, data: bytes) -> None:
    #     # await self.job_queue.async_q.put(data)
    #     def _write() -> None:
    #         # os.close(self.reader_fd)
    #         # fd = os.fdopen(self.writer_fd, "wb")
    #         # fd.write(data)
    #         # fd.close()

    #         os.write(self.writer_fd, data)

    #     await asyncio.get_running_loop().run_in_executor(None, _write)

    @classmethod
    async def read_pipe(cls, reader_fd: int) -> bytes:
        def _read() -> bytes:
            return os.read(reader_fd, 1000)

        return await asyncio.get_running_loop().run_in_executor(None, _read)

    async def write_pipe(self, data: bytes) -> None:
        def _write() -> None:
            os.write(self.writer_fd, data)

        await asyncio.get_running_loop().run_in_executor(None, _write)

    @classmethod
    async def run_pipe_task(cls, raw_data: bytes):
        task = _deserialize(raw_data)
        await task.run()

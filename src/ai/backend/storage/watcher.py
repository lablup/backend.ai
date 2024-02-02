from __future__ import annotations

import asyncio
import logging
import os
import traceback
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Sequence, Type

import attrs
import zmq
import zmq.asyncio

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
            loop.call_exception_handler({
                "message": "unhandled exception during loop shutdown",
                "exception": task.exception(),
                "task": task,
            })


# Using extra_procs
def main_job(
    worker_pidx: int,
    insock_prefix: str | None,
    outsock_prefix: str | None,
    intr_event: Any,
    pidx: int,
    args: Sequence[Any],
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        proc = WatcherProcess(worker_pidx, insock_prefix, outsock_prefix)
        loop.run_until_complete(proc.main())
    except Exception:
        print("Error ====", flush=True)
        print(traceback.format_exc(), flush=True)
        raise
    finally:
        try:
            loop.run_until_complete(cancel_all_tasks(loop))
            loop.run_until_complete(loop.shutdown_asyncgens())
            try:
                loop.run_until_complete(loop.shutdown_default_executor())
            except (AttributeError, NotImplementedError):  # for uvloop
                pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)


class AbstractTask(metaclass=ABCMeta):
    name: ClassVar[str] = "undefined"

    @abstractmethod
    async def run(self) -> Any:
        pass

    @classmethod
    def deserialize_from_request(cls, raw_data: Request) -> AbstractTask:
        serializer_name = str(raw_data.header, "utf8")
        values: tuple = msgpack.unpackb(raw_data.body)
        serializer_cls = SERIALIZER_MAP[serializer_name]
        return serializer_cls.deserialize(values)

    def serialize_to_request(self) -> Request:
        assert self.name in SERIALIZER_MAP
        header = bytes(self.name, "utf8")
        return Request(header, self.serialize())

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

    async def run(self) -> Any:
        os.chown(self.directory, self.uid, self.gid)

    def serialize(self) -> bytes:
        return msgpack.packb((
            self.directory,
            self.uid,
            self.gid,
        ))

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

    async def run(self) -> Any:
        return await _mount(
            self.mount_path,
            self.fs_location,
            self.fs_type,
            self.cmd_options,
            self.edit_fstab,
            self.fstab_path,
            self.mount_prefix,
        )

    @classmethod
    def from_event(
        cls, event: DoVolumeMountEvent, *, mount_path: Path, mount_prefix: str | None = None
    ) -> MountTask:
        return MountTask(
            str(mount_path),
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
        return msgpack.packb((
            self.mount_path,
            str(self.quota_scope_id),
            self.fs_location,
            self.fs_type,
            self.cmd_options,
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
            self.mount_prefix,
        ))

    @classmethod
    def deserialize(cls, values: tuple) -> MountTask:
        return MountTask(
            values[0],
            QuotaScopeID.parse(values[1]),
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
            values[7],
            values[8],
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
    timeout: float | None = attrs.field(default=None)

    async def run(self) -> Any:
        did_umount = await _umount(
            self.mount_path,
            edit_fstab=self.edit_fstab,
            fstab_path=self.fstab_path,
            timeout_sec=self.timeout,
        )
        if not did_umount:
            return f"{self.mount_path} not exists. Skip umount."
        return None

    @classmethod
    def from_event(
        cls,
        event: DoVolumeUnmountEvent,
        *,
        mount_path: Path,
        mount_prefix: str | None = None,
        timeout: float | None = None,
    ) -> UmountTask:
        return UmountTask(
            str(mount_path),
            event.quota_scope_id,
            event.scaling_group,
            event.edit_fstab,
            event.fstab_path,
            mount_prefix,
            timeout,
        )

    def serialize(self) -> bytes:
        return msgpack.packb((
            self.mount_path,
            str(self.quota_scope_id),
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
            self.mount_prefix,
            self.timeout,
        ))

    @classmethod
    def deserialize(cls, values: tuple) -> UmountTask:
        return UmountTask(
            values[0],
            QuotaScopeID.parse(values[1]),
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
        )


SERIALIZER_MAP: dict[str, Type[AbstractTask]] = {
    MountTask.name: MountTask,
    UmountTask.name: UmountTask,
    ChownTask.name: ChownTask,
}


@attrs.define(slots=True)
class Request:
    header: bytes = attrs.field()
    body: bytes = attrs.field()

    def serialize(self) -> tuple[bytes, bytes]:
        return (self.header, self.body)

    @classmethod
    def deserialize(cls, data: tuple[bytes, bytes]) -> Request:
        return Request(data[0], data[1])


@attrs.define(slots=True)
class Response:
    succeeded: bool = attrs.field()
    body: str = attrs.field()

    def serialize(self) -> tuple[bytes, bytes]:
        return (bool.to_bytes(self.succeeded), bytes(self.body, "utf8"))

    @classmethod
    def deserialize(cls, data: tuple[bytes, bytes]) -> Response:
        return Response(bool.from_bytes(data[0]), str(data[1], "utf8"))


def get_zmq_socket_file_path(path: str | Path | None, pidx: int) -> str:
    if path is None:
        raise ValueError("Socket path should not be None")
    return f"ipc://{path}-{pidx}"


class Protocol:
    @classmethod
    async def request(cls, insock: zmq.asyncio.Socket, data: Request) -> None:
        if insock.closed:
            raise asyncio.CancelledError
        await insock.send_multipart(data.serialize())

    @classmethod
    async def listen_to_request(cls, insock: zmq.asyncio.Socket) -> Request:
        if insock.closed:
            raise asyncio.CancelledError
        data = await insock.recv_multipart()
        if (data_len := len(data)) != 2:
            raise ValueError(f"data length for request should be 2, not {data_len}")
        return Request.deserialize((data[0], data[1]))

    @classmethod
    async def respond(cls, outsock: zmq.asyncio.Socket, data: Response) -> None:
        if outsock.closed:
            raise asyncio.CancelledError
        await outsock.send_multipart(data.serialize())

    @classmethod
    async def listen_to_response(cls, outsock: zmq.asyncio.Socket) -> Response:
        if outsock.closed:
            raise asyncio.CancelledError
        data = await outsock.recv_multipart()
        if (data_len := len(data)) != 2:
            raise ValueError(f"data length for respond should be 2, not {data_len}")
        return Response.deserialize((data[0], data[1]))


class WatcherProcess:
    def __init__(
        self,
        pidx: int,
        input_sock_prefix: str | None,
        output_sock_prefix: str | None,
    ) -> None:
        self.pidx = pidx
        zctx = zmq.asyncio.Context()
        self.insock = zctx.socket(zmq.PULL)
        self.insock.bind(get_zmq_socket_file_path(input_sock_prefix, self.pidx))

        self.outsock = zctx.socket(zmq.PUSH)
        self.outsock.bind(get_zmq_socket_file_path(output_sock_prefix, self.pidx))

    async def close(self) -> None:
        self.insock.close()
        self.outsock.close()

    async def ack(self) -> None:
        await Protocol.respond(self.outsock, Response(True, ""))

    async def respond(self, succeeded: bool, data: str) -> None:
        await Protocol.respond(self.outsock, Response(succeeded, data))

    async def main(self) -> None:
        try:
            while True:
                client_request = await Protocol.listen_to_request(self.insock)

                try:
                    task = AbstractTask.deserialize_from_request(client_request)
                    result = await task.run()
                except Exception as e:
                    log.exception(f"Error in watcher task. (e: {e})")
                    await self.respond(False, repr(e))
                else:
                    if result is not None:
                        await self.respond(True, str(result))
                    else:
                        await self.ack()
        finally:
            await self.close()


class WatcherClient:
    def __init__(
        self,
        pidx: int,
        input_sock_prefix: str | None,
        output_sock_prefix: str | None,
    ) -> None:
        self.pidx = pidx
        zctx = zmq.asyncio.Context()
        self.input_sock = zctx.socket(zmq.PUSH)
        self.input_sock_addr = get_zmq_socket_file_path(input_sock_prefix, self.pidx)
        self.output_sock = zctx.socket(zmq.PULL)
        self.output_sock_addr = get_zmq_socket_file_path(output_sock_prefix, self.pidx)
        self.result_queue: asyncio.Queue[Response] = asyncio.Queue(maxsize=128)
        self.output_listening_task: asyncio.Task | None = None

    async def init(self) -> None:
        self.input_sock.connect(self.input_sock_addr)
        self.input_sock.setsockopt(zmq.LINGER, 50)
        self.output_sock.connect(self.output_sock_addr)
        self.output_sock.setsockopt(zmq.LINGER, 50)
        loop = asyncio.get_running_loop()
        self.output_listening_task = loop.create_task(self._listen_output())

    async def close(self) -> None:
        if self.output_listening_task and not self.output_listening_task.done():
            self.output_listening_task.cancel()
            await self.output_listening_task
        if self.input_sock:
            self.input_sock.close()
        if self.output_sock:
            self.output_sock.close()

    async def _listen_output(self) -> None:
        while True:
            try:
                data = await Protocol.listen_to_response(self.output_sock)
                try:
                    await self.result_queue.put(data)
                except asyncio.QueueFull:
                    pass
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception:
                log.exception("unexpected error")
                break

    async def request(self, data: Request) -> Response:
        try:
            await Protocol.request(self.input_sock, data)
            result = await self.result_queue.get()
            self.result_queue.task_done()
            return result
        except asyncio.CancelledError:
            raise

    async def request_task(self, task: AbstractTask) -> Response:
        return await self.request(task.serialize_to_request())

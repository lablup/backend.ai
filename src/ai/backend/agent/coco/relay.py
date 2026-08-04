from __future__ import annotations

import asyncio
import errno
import json
import logging
import os
import socket
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Final

from ai.backend.common.kernel_runner import CHANNEL_PROTOCOL_VERSION
from ai.backend.logging import BraceStyleAdapter

from .errors import RawCircuitRefused, RelayUnavailable

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _splice_unavailable(*_args: object, **_kwargs: object) -> int:
    raise RelayUnavailable(extra_msg=f"os.splice is absent on {sys.platform}")


_splice: Final[Callable[..., int]] = getattr(os, "splice", _splice_unavailable)
_SPLICE_FLAGS: Final[int] = getattr(os, "SPLICE_F_NONBLOCK", 0) | getattr(os, "SPLICE_F_MOVE", 0)

PIPE_CAPACITY: Final = 1 << 20
HEADER_LIMIT: Final = 4096
HEADER_TIMEOUT: Final = 10.0
GUEST_DIAL_TIMEOUT: Final = 10.0
ACCEPT_BACKLOG: Final = 64


class Pump:
    __slots__ = ("_credit", "_read_end", "_sink", "_source", "_write_end")

    def __init__(
        self, source: socket.socket, sink: socket.socket, credit: Callable[[int], None]
    ) -> None:
        self._source = source.fileno()
        self._sink = sink.fileno()
        self._credit = credit
        self._read_end, self._write_end = os.pipe()
        os.set_blocking(self._read_end, False)
        os.set_blocking(self._write_end, False)

    async def run(self, loop: asyncio.AbstractEventLoop) -> None:
        try:
            while True:
                drawn = await _move(loop, self._source, self._write_end)
                if drawn == 0:
                    return
                self._credit(drawn)
                while drawn > 0:
                    pushed = await _move(loop, self._read_end, self._sink)
                    if pushed == 0:
                        return
                    drawn -= pushed
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        finally:
            os.close(self._read_end)
            os.close(self._write_end)


async def _move(loop: asyncio.AbstractEventLoop, src: int, dst: int) -> int:
    stalled_on_source = True
    while True:
        try:
            return _splice(src, dst, PIPE_CAPACITY, flags=_SPLICE_FLAGS)
        except BlockingIOError:
            if stalled_on_source:
                await _ready(loop, src, loop.add_reader, loop.remove_reader)
            else:
                await _ready(loop, dst, loop.add_writer, loop.remove_writer)
            stalled_on_source = not stalled_on_source


async def _ready(
    loop: asyncio.AbstractEventLoop,
    fd: int,
    arm: Callable[..., None],
    disarm: Callable[[int], bool],
) -> None:
    waiter = loop.create_future()
    arm(fd, lambda: None if waiter.done() else waiter.set_result(None))
    try:
        await waiter
    finally:
        disarm(fd)


async def _read_header(loop: asyncio.AbstractEventLoop, sock: socket.socket) -> tuple[bytes, bytes]:
    buf = bytearray()
    while True:
        try:
            chunk = sock.recv(HEADER_LIMIT)
        except BlockingIOError:
            await _ready(loop, sock.fileno(), loop.add_reader, loop.remove_reader)
            continue
        if not chunk:
            raise ValueError("the circuit request was absent")
        buf += chunk
        border = buf.find(b"\n")
        if border >= 0:
            return bytes(buf[:border]), bytes(buf[border + 1 :])
        if len(buf) > HEADER_LIMIT:
            raise ValueError("the circuit request was oversized")


async def _send_all(loop: asyncio.AbstractEventLoop, sock: socket.socket, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        try:
            sent = sock.send(view)
        except BlockingIOError:
            await _ready(loop, sock.fileno(), loop.add_writer, loop.remove_writer)
            continue
        view = view[sent:]


async def _dial(loop: asyncio.AbstractEventLoop, host: str, port: int) -> socket.socket:
    family, kind, proto, _, address = (await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM))[
        0
    ]
    sock = socket.socket(family, kind, proto)
    try:
        sock.setblocking(False)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        code = sock.connect_ex(address)
        if code in (errno.EINPROGRESS, errno.EWOULDBLOCK):
            await _ready(loop, sock.fileno(), loop.add_writer, loop.remove_writer)
            code = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if code:
            raise OSError(code, os.strerror(code))
    except BaseException:
        sock.close()
        raise
    return sock


async def _refuse(loop: asyncio.AbstractEventLoop, sock: socket.socket, reason: str) -> None:
    log.warning("coco: relay refused a circuit — {}", reason)
    try:
        await _send_all(
            loop, sock, json.dumps({"ok": False, "error": reason}).encode("utf-8") + b"\n"
        )
    except OSError:
        pass


@dataclass
class ChannelFlow:
    kernel_id: str
    session_id: str
    circuits: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    last_activity: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class Circuit:
    guest_host: str
    guest_port: int
    session_id: str


CircuitResolver = Callable[[str, int], Awaitable[Circuit]]


class ChannelRelay:
    def __init__(self, bind_host: str, bind_port: int, resolve: CircuitResolver) -> None:
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._resolve = resolve
        self._listener: socket.socket | None = None
        self._acceptor: asyncio.Task[None] | None = None
        self._circuits: set[asyncio.Task[None]] = set()
        self._flows: dict[str, ChannelFlow] = {}

    @property
    def flows(self) -> dict[str, ChannelFlow]:
        return self._flows

    def forget(self, kernel_id: str) -> None:
        self._flows.pop(kernel_id, None)

    # Nothing here may become an asyncio transport: a transport owns its fd for as long as it
    # lives, and uvloop then rejects the add_reader/add_writer that splicing the fd depends on.
    async def start(self) -> None:
        if not hasattr(os, "splice"):
            raise RelayUnavailable(
                extra_msg="this kernel cannot move bytes without reading them; the relay refuses"
                " to fall back to a readable pump"
            )
        listener = socket.create_server(
            (self._bind_host, self._bind_port),
            family=socket.AF_INET6 if ":" in self._bind_host else socket.AF_INET,
            backlog=ACCEPT_BACKLOG,
        )
        listener.setblocking(False)
        self._listener = listener
        self._acceptor = asyncio.create_task(self._serve(listener))
        log.info("coco: channel relay listening on {}:{}", self._bind_host, self._bind_port)

    async def close(self) -> None:
        if self._acceptor is not None:
            self._acceptor.cancel()
            await asyncio.gather(self._acceptor, return_exceptions=True)
            self._acceptor = None
        live = list(self._circuits)
        for task in live:
            task.cancel()
        await asyncio.gather(*live, return_exceptions=True)
        if self._listener is not None:
            self._listener.close()
            self._listener = None

    async def _serve(self, listener: socket.socket) -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                near, _ = await loop.sock_accept(listener)
            except OSError as e:
                log.warning("coco: relay stopped accepting circuits: {}", e)
                return
            near.setblocking(False)
            near.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            task = asyncio.create_task(self._circuit(near))
            self._circuits.add(task)
            task.add_done_callback(self._circuits.discard)

    async def _route(
        self, loop: asyncio.AbstractEventLoop, near: socket.socket
    ) -> tuple[str, Circuit, bytes] | None:
        kernel_id = ""
        try:
            async with asyncio.timeout(HEADER_TIMEOUT):
                line, spilled = await _read_header(loop, near)
            request = json.loads(line)
            if request.get("v") != CHANNEL_PROTOCOL_VERSION:
                raise ValueError(f"unknown channel protocol {request.get('v')!r}")
            kernel_id = str(request["kernel"])
            return kernel_id, await self._resolve(kernel_id, int(request["port"])), spilled
        except RawCircuitRefused as e:
            await _refuse(loop, near, str(e))
        except (TimeoutError, ValueError, KeyError, TypeError) as e:
            await _refuse(loop, near, f"the relay could not route this circuit: {e}")
        except Exception as e:
            await _refuse(loop, near, f"the relay could not resolve kernel {kernel_id}: {e}")
        return None

    async def _circuit(self, near: socket.socket) -> None:
        loop = asyncio.get_running_loop()
        far: socket.socket | None = None
        kernel_id = ""
        try:
            route = await self._route(loop, near)
            if route is None:
                return
            kernel_id, circuit, spilled = route
            try:
                async with asyncio.timeout(GUEST_DIAL_TIMEOUT):
                    far = await _dial(loop, circuit.guest_host, circuit.guest_port)
            except (OSError, TimeoutError) as e:
                await _refuse(loop, near, f"the guest did not answer on {circuit.guest_port}: {e}")
                return
            await _send_all(loop, near, b'{"ok": true}\n')
            if spilled:
                await _send_all(loop, far, spilled)
            await self._pump(kernel_id, circuit, near, far)
        except OSError as e:
            log.debug("coco: relay circuit for {} ended: {}", kernel_id, e)
        finally:
            near.close()
            if far is not None:
                far.close()

    async def _pump(
        self, kernel_id: str, circuit: Circuit, near: socket.socket, far: socket.socket
    ) -> None:
        flow = self._flows.setdefault(
            kernel_id, ChannelFlow(kernel_id=kernel_id, session_id=circuit.session_id)
        )
        flow.circuits += 1
        flow.last_activity = time.monotonic()

        def inward(moved: int) -> None:
            flow.bytes_in += moved
            flow.last_activity = time.monotonic()

        def outward(moved: int) -> None:
            flow.bytes_out += moved
            flow.last_activity = time.monotonic()

        loop = asyncio.get_running_loop()
        tasks = [
            asyncio.create_task(Pump(near, far, inward).run(loop)),
            asyncio.create_task(Pump(far, near, outward).run(loop)),
        ]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            flow.circuits -= 1
            flow.last_activity = time.monotonic()

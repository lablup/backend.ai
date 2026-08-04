from __future__ import annotations

import asyncio
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

def _splice_unavailable(*args: object, **kwargs: object) -> int:
    raise RelayUnavailable(extra_msg=f"os.splice is absent on {sys.platform}")


_splice: Final[Callable[..., int]] = getattr(os, "splice", _splice_unavailable)
_SPLICE_FLAGS: Final[int] = getattr(os, "SPLICE_F_NONBLOCK", 0) | getattr(os, "SPLICE_F_MOVE", 0)

PIPE_CAPACITY: Final = 1 << 20
HEADER_LIMIT: Final = 4096
HEADER_TIMEOUT: Final = 10.0
GUEST_DIAL_TIMEOUT: Final = 10.0


class Pump:
    __slots__ = ("_source", "_sink", "_read_end", "_write_end", "_moved")

    def __init__(self, source: socket.socket, sink: socket.socket) -> None:
        self._source = source.fileno()
        self._sink = sink.fileno()
        self._read_end, self._write_end = os.pipe()
        os.set_blocking(self._read_end, False)
        os.set_blocking(self._write_end, False)
        self._moved = 0

    @property
    def moved(self) -> int:
        return self._moved

    async def run(self, loop: asyncio.AbstractEventLoop) -> None:
        try:
            while True:
                drawn = await _move(loop, self._source, self._write_end)
                if drawn == 0:
                    return
                self._moved += drawn
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
        self._server: asyncio.Server | None = None
        self._flows: dict[str, ChannelFlow] = {}

    @property
    def flows(self) -> dict[str, ChannelFlow]:
        return self._flows

    def forget(self, kernel_id: str) -> None:
        self._flows.pop(kernel_id, None)

    async def start(self) -> None:
        if not hasattr(os, "splice"):
            raise RelayUnavailable(
                extra_msg="this kernel cannot move bytes without reading them; the relay refuses"
                " to fall back to a readable pump"
            )
        self._server = await asyncio.start_server(
            self._accept, self._bind_host, self._bind_port, reuse_address=True
        )
        log.info("coco: channel relay listening on {}:{}", self._bind_host, self._bind_port)

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _accept(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        circuit: Circuit | None = None
        kernel_id = ""
        try:
            async with asyncio.timeout(HEADER_TIMEOUT):
                line = await reader.readline()
            if not line or len(line) > HEADER_LIMIT:
                raise ValueError("the circuit request was absent or oversized")
            request = json.loads(line)
            if request.get("v") != CHANNEL_PROTOCOL_VERSION:
                raise ValueError(f"unknown channel protocol {request.get('v')!r}")
            kernel_id = str(request["kernel"])
            circuit = await self._resolve(kernel_id, int(request["port"]))
        except RawCircuitRefused as e:
            await _refuse(writer, str(e))
            return
        except (TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            await _refuse(writer, f"the relay could not route this circuit: {e}")
            return
        except Exception as e:
            await _refuse(writer, f"the relay could not resolve kernel {kernel_id}: {e}")
            return
        try:
            async with asyncio.timeout(GUEST_DIAL_TIMEOUT):
                guest = await asyncio.open_connection(circuit.guest_host, circuit.guest_port)
        except (OSError, TimeoutError) as e:
            await _refuse(writer, f"the guest did not answer on {circuit.guest_port}: {e}")
            return
        writer.write(b'{"ok": true}\n')
        await writer.drain()
        await self._splice(kernel_id, circuit, writer, guest[1])

    async def _splice(
        self,
        kernel_id: str,
        circuit: Circuit,
        downstream: asyncio.StreamWriter,
        upstream: asyncio.StreamWriter,
    ) -> None:
        near = downstream.get_extra_info("socket")
        far = upstream.get_extra_info("socket")
        flow = self._flows.setdefault(
            kernel_id, ChannelFlow(kernel_id=kernel_id, session_id=circuit.session_id)
        )
        flow.circuits += 1
        flow.last_activity = time.monotonic()
        inbound = Pump(near, far)
        outbound = Pump(far, near)
        loop = asyncio.get_running_loop()
        tasks = [asyncio.create_task(inbound.run(loop)), asyncio.create_task(outbound.run(loop))]
        try:
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        except OSError as e:
            log.debug("coco: relay circuit for {} ended: {}", kernel_id, e)
        finally:
            flow.circuits -= 1
            flow.bytes_in += inbound.moved
            flow.bytes_out += outbound.moved
            flow.last_activity = time.monotonic()
            for stream in (downstream, upstream):
                stream.close()


async def _refuse(writer: asyncio.StreamWriter, reason: str) -> None:
    log.warning("coco: relay refused a circuit — {}", reason)
    try:
        writer.write(json.dumps({"ok": False, "error": reason}).encode("utf-8") + b"\n")
        await writer.drain()
    except OSError:
        pass
    finally:
        writer.close()

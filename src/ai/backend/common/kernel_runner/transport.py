from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import ssl
import struct
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, override

import zmq
import zmq.asyncio

from ai.backend.logging import BraceStyleAdapter

from .errors import ChannelIdentityRefused, ChannelNotEstablished, InvalidSocket
from .vocabulary import CHANNEL_PROTOCOL_VERSION

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_zctx: zmq.asyncio.Context | None = None
_COUNT: Final = struct.Struct("!I")
_MAX_FRAME: Final = 64 * (2**20)
DIAL_TIMEOUT: Final = 20.0


class RunnerTransport(metaclass=ABCMeta):
    @abstractmethod
    async def send_multipart(self, msg_parts: Sequence[bytes]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def recv_multipart(self) -> list[bytes]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class ZeroMQTransport(RunnerTransport):
    def __init__(self, in_addr: str, out_addr: str) -> None:
        self._in_addr = in_addr
        self._out_addr = out_addr
        self._in_sock = self._dial(zmq.PUSH, in_addr)
        self._out_sock = self._dial(zmq.PULL, out_addr)

    @staticmethod
    def _context() -> zmq.asyncio.Context:
        global _zctx
        if _zctx is None:
            _zctx = zmq.asyncio.Context()
        return _zctx

    def _dial(self, socket_type: int, addr: str) -> zmq.asyncio.Socket:
        sock = self._context().socket(socket_type)
        sock.connect(addr)
        sock.setsockopt(zmq.LINGER, 50)
        return sock

    def _recreate(self) -> None:
        self._in_sock = self._dial(zmq.PUSH, self._in_addr)
        self._out_sock = self._dial(zmq.PULL, self._out_addr)

    @override
    async def send_multipart(self, msg_parts: Sequence[bytes]) -> None:
        try:
            await self._in_sock.send_multipart(msg_parts)
        except zmq.ZMQError as e:
            if e.errno not in (zmq.ENOTSOCK, zmq.ETERM):
                raise
            log.warning("recreating the runner sockets ({}, {!r})", self._in_addr, e)
            self._recreate()
            await self._in_sock.send_multipart(msg_parts)

    @override
    async def recv_multipart(self) -> list[bytes]:
        try:
            return await self._out_sock.recv_multipart()
        except zmq.ZMQError as e:
            if e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                raise InvalidSocket from e
            raise

    @override
    def close(self) -> None:
        for sock in (self._in_sock, self._out_sock):
            try:
                sock.close()
            except zmq.ZMQError:
                pass


@dataclass(frozen=True)
class ChannelEndpoint:
    relay_host: str
    relay_port: int
    kernel_id: str
    guest_port: int
    certificate_fingerprint: str
    token: str


class FramedTransport(RunnerTransport):
    def __init__(self, endpoint: ChannelEndpoint) -> None:
        self._endpoint = endpoint
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._epoch = -1
        self._lock = asyncio.Lock()

    @property
    def epoch(self) -> int:
        return self._epoch

    async def _dial(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        endpoint = self._endpoint
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        try:
            async with asyncio.timeout(DIAL_TIMEOUT):
                reader, writer = await asyncio.open_connection(
                    endpoint.relay_host, endpoint.relay_port
                )
                writer.write(
                    json.dumps({
                        "v": CHANNEL_PROTOCOL_VERSION,
                        "kernel": endpoint.kernel_id,
                        "port": endpoint.guest_port,
                    }).encode("utf-8")
                    + b"\n"
                )
                await writer.drain()
                ack = json.loads(await reader.readline() or b"{}")
                if not ack.get("ok"):
                    raise ChannelNotEstablished(
                        extra_msg=f"the relay refused the circuit: {ack.get('error')}"
                    )
                await writer.start_tls(context)
                peer = writer.get_extra_info("ssl_object").getpeercert(True)
                presented = hashlib.sha256(peer).hexdigest()
                if not secrets.compare_digest(presented, endpoint.certificate_fingerprint):
                    raise ChannelIdentityRefused(
                        extra_msg=f"the guest presented {presented}, not the vouched identity"
                    )
                nonce = secrets.token_hex(32)
                await _write_frames(
                    writer, [json.dumps({"token": endpoint.token, "nonce": nonce}).encode("utf-8")]
                )
                hello = json.loads((await _read_frames(reader))[0])
                if not hello.get("ok"):
                    raise ChannelIdentityRefused(
                        extra_msg=f"the guest refused the dial: {hello.get('error')}"
                    )
                epoch = int(hello["epoch"])
                if epoch <= self._epoch:
                    raise ChannelIdentityRefused(
                        extra_msg=f"the guest replayed connection epoch {epoch}"
                    )
                self._epoch = epoch
        except (OSError, TimeoutError, ValueError, KeyError, ssl.SSLError) as e:
            raise ChannelNotEstablished(
                extra_msg=f"{endpoint.relay_host}:{endpoint.relay_port} — {e}"
            ) from e
        return reader, writer

    async def _ensure(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        async with self._lock:
            if self._writer is None or self._writer.is_closing():
                self._reader, self._writer = await self._dial()
            assert self._reader is not None and self._writer is not None
            return self._reader, self._writer

    def _drop(self) -> None:
        if self._writer is not None:
            self._writer.close()
        self._reader = None
        self._writer = None

    @override
    async def send_multipart(self, msg_parts: Sequence[bytes]) -> None:
        _, writer = await self._ensure()
        try:
            await _write_frames(writer, msg_parts)
        except (OSError, ssl.SSLError) as e:
            self._drop()
            raise ChannelNotEstablished(extra_msg=f"the channel dropped while sending: {e}") from e

    @override
    async def recv_multipart(self) -> list[bytes]:
        reader, _ = await self._ensure()
        try:
            return await _read_frames(reader)
        except (OSError, ssl.SSLError, asyncio.IncompleteReadError) as e:
            self._drop()
            raise ChannelNotEstablished(extra_msg=f"the channel dropped while reading: {e}") from e

    @override
    def close(self) -> None:
        self._drop()


async def _write_frames(writer: asyncio.StreamWriter, parts: Sequence[bytes]) -> None:
    writer.write(_COUNT.pack(len(parts)))
    for part in parts:
        writer.write(_COUNT.pack(len(part)))
        writer.write(part)
    await writer.drain()


async def _read_frames(reader: asyncio.StreamReader) -> list[bytes]:
    count = _COUNT.unpack(await reader.readexactly(_COUNT.size))[0]
    parts: list[bytes] = []
    for _ in range(count):
        size = _COUNT.unpack(await reader.readexactly(_COUNT.size))[0]
        if size > _MAX_FRAME:
            raise InvalidSocket(extra_msg=f"a {size}-byte frame exceeds the channel limit")
        parts.append(await reader.readexactly(size))
    return parts

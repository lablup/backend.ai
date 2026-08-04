from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import secrets
import ssl
import struct
import tarfile
import tempfile
import urllib.request
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any, Final

import zmq
import zmq.asyncio

from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger())

CHANNEL_PORT: Final = 2010
CHANNEL_URI_ENV: Final = "BACKENDAI_CC_CHANNEL_URI"
PROFILE_PATH: Final = Path("/run/backend.ai/profile.json")
SELF_ENCRYPTING: Final = frozenset({"sshd", "ssh", "sftp"})
BUNDLE_MEMBERS: Final = ("channel/key.pem", "channel/cert.pem", "channel/token")
NONCE_HISTORY: Final = 512
NONCE_LENGTH: Final = 64
REPL_IN: Final = "tcp://127.0.0.1:2000"
REPL_OUT: Final = "tcp://127.0.0.1:2001"
FETCH_TIMEOUT: Final = 60
CHUNK: Final = 65536
_COUNT: Final = struct.Struct("!I")
_MAX_FRAME: Final = 64 * (2**20)


class ChannelUnavailable(RuntimeError):
    pass


def terminates(name: str) -> bool:
    return name not in SELF_ENCRYPTING


async def _read_frames(reader: asyncio.StreamReader) -> list[bytes]:
    count = _COUNT.unpack(await reader.readexactly(_COUNT.size))[0]
    parts: list[bytes] = []
    for _ in range(count):
        size = _COUNT.unpack(await reader.readexactly(_COUNT.size))[0]
        if size > _MAX_FRAME:
            raise ChannelUnavailable(f"a {size}-byte frame exceeds the channel limit")
        parts.append(await reader.readexactly(size))
    return parts


async def _write_frames(writer: asyncio.StreamWriter, parts: Sequence[bytes]) -> None:
    writer.write(_COUNT.pack(len(parts)))
    for part in parts:
        writer.write(_COUNT.pack(len(part)))
        writer.write(part)
    await writer.drain()


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while chunk := await reader.read(CHUNK):
            writer.write(chunk)
            await writer.drain()
    except OSError:
        pass
    finally:
        writer.close()


def _fetch(api: str, resource: str) -> dict[str, bytes]:
    url = f"{api}/cdh/resource/{resource}"
    try:
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as response:
            payload = response.read()
    except OSError as e:
        raise ChannelUnavailable(f"the broker released no channel identity from {url}: {e}") from e
    if not payload:
        raise ChannelUnavailable(f"the broker released {resource} as zero bytes")
    members: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as bundle:
            for name in BUNDLE_MEMBERS:
                extracted = bundle.extractfile(name)
                if extracted is None:
                    raise KeyError(name)
                members[name] = extracted.read()
    except (KeyError, tarfile.TarError) as e:
        raise ChannelUnavailable(f"the released channel bundle lacks {e}") from e
    if not all(members.values()):
        raise ChannelUnavailable("the released channel bundle carries an empty member")
    return members


class TransportTerminator:
    def __init__(self, service_ports: Sequence[tuple[str, int, int]] = ()) -> None:
        self._service_ports = [entry for entry in service_ports if terminates(entry[0])]
        self._resource = os.environ.get(CHANNEL_URI_ENV, "")
        self._api = ""
        self._token = b""
        self._epoch = 0
        self._nonces: OrderedDict[str, None] = OrderedDict()
        self._context: ssl.SSLContext | None = None
        self._keydir: Path | None = None
        self._servers: list[asyncio.Server] = []
        self._zctx: zmq.asyncio.Context | None = None
        self._live: asyncio.Task[Any] | None = None

    async def start(self) -> None:
        if not self._resource or not PROFILE_PATH.is_file():
            return
        try:
            profile = json.loads(await asyncio.to_thread(PROFILE_PATH.read_text))
            self._api = str(profile["api"])
        except (OSError, ValueError, KeyError) as e:
            raise ChannelUnavailable(f"the guest profile names no broker: {e}") from e
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.verify_mode = ssl.CERT_NONE
        self._context = context
        await self._install()
        self._zctx = zmq.asyncio.Context()
        self._servers.append(
            await asyncio.start_server(self._channel, "0.0.0.0", CHANNEL_PORT, ssl=context)
        )
        log.info("terminator: the guest channel terminates on {}", CHANNEL_PORT)
        for name, local, listen in self._service_ports:
            self._servers.append(
                await asyncio.start_server(
                    partial(self._proxy, local), "0.0.0.0", listen, ssl=context
                )
            )
            log.info("terminator: {} terminates on {} for {}", name, listen, local)

    async def rebind(self) -> None:
        if self._context is not None:
            await self._install()

    async def stop(self) -> None:
        if self._live is not None:
            self._live.cancel()
            self._live = None
        for server in self._servers:
            server.close()
        self._servers.clear()
        if self._zctx is not None:
            self._zctx.destroy(linger=0)
            self._zctx = None

    async def _install(self) -> None:
        if self._context is None:
            raise ChannelUnavailable("no transport context to install a released identity into")
        members = await asyncio.to_thread(_fetch, self._api, self._resource)
        if self._keydir is None:
            self._keydir = Path(tempfile.mkdtemp(prefix="bai-channel-"))
        key = self._keydir / "key.pem"
        cert = self._keydir / "cert.pem"
        try:
            key.write_bytes(members["channel/key.pem"])
            key.chmod(0o600)
            cert.write_bytes(members["channel/cert.pem"])
            self._context.load_cert_chain(cert, key)
        finally:
            key.unlink(missing_ok=True)
            cert.unlink(missing_ok=True)
        self._token = members["channel/token"].strip()

    def _admit(self, hello: Mapping[str, Any]) -> str | None:
        offered = str(hello.get("token", "")).encode("utf-8")
        nonce = str(hello.get("nonce", ""))
        if not secrets.compare_digest(offered, self._token):
            return "the dial carried an unknown channel token"
        if len(nonce) != NONCE_LENGTH or nonce in self._nonces:
            return "the dial carried a malformed or replayed nonce"
        self._nonces[nonce] = None
        while len(self._nonces) > NONCE_HISTORY:
            self._nonces.popitem(last=False)
        return None

    async def _greet(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
        refusal = self._admit(json.loads((await _read_frames(reader))[0]))
        if refusal is not None:
            await _write_frames(
                writer, [json.dumps({"ok": False, "error": refusal}).encode("utf-8")]
            )
            log.warning("terminator: {}", refusal)
            return False
        epoch = self._epoch
        self._epoch += 1
        await _write_frames(writer, [json.dumps({"ok": True, "epoch": epoch}).encode("utf-8")])
        return True

    async def _channel(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            if not await self._greet(reader, writer):
                return
            displaced = self._live
            if displaced is not None:
                displaced.cancel()
                await asyncio.gather(displaced, return_exceptions=True)
            self._live = asyncio.current_task()
            await self._bridge(reader, writer)
        except (OSError, EOFError, ValueError, IndexError, ChannelUnavailable) as e:
            log.warning("terminator: the channel dropped ({})", e)
        finally:
            if self._live is asyncio.current_task():
                self._live = None
            writer.close()

    async def _bridge(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if self._zctx is None:
            raise ChannelUnavailable("no message context to bridge a client connection onto")
        push = self._zctx.socket(zmq.PUSH)
        push.setsockopt(zmq.LINGER, 0)
        push.connect(REPL_IN)
        pull = self._zctx.socket(zmq.PULL)
        pull.setsockopt(zmq.LINGER, 0)
        pull.connect(REPL_OUT)
        inbound = asyncio.create_task(self._inbound(reader, push))
        outbound = asyncio.create_task(self._outbound(pull, writer))
        try:
            await asyncio.wait({inbound, outbound}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            inbound.cancel()
            outbound.cancel()
            await asyncio.gather(inbound, outbound, return_exceptions=True)
            push.close()
            pull.close()

    async def _inbound(self, reader: asyncio.StreamReader, push: zmq.asyncio.Socket) -> None:
        try:
            while True:
                await push.send_multipart(await _read_frames(reader))
        except (OSError, EOFError, ChannelUnavailable, zmq.ZMQError) as e:
            log.debug("terminator: the inbound pump stopped ({})", e)

    async def _outbound(self, pull: zmq.asyncio.Socket, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                await _write_frames(writer, await pull.recv_multipart())
        except (OSError, zmq.ZMQError) as e:
            log.debug("terminator: the outbound pump stopped ({})", e)

    async def _proxy(
        self, local: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            upstream, upwriter = await asyncio.open_connection("127.0.0.1", local)
        except OSError as e:
            log.warning("terminator: nothing answers on 127.0.0.1:{} ({})", local, e)
            writer.close()
            return
        await asyncio.gather(
            _pipe(reader, upwriter), _pipe(upstream, writer), return_exceptions=True
        )

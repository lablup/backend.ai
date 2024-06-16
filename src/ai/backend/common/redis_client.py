import asyncio
import logging
import socket
from typing import Any, AsyncContextManager, Final, Sequence

import hiredis

from .logging import BraceStyleAdapter
from .types import EtcdRedisConfig, aobject

__all__ = (
    "RedisClient",
    "RedisConnection",
)


_keepalive_options: dict[int, int] = {}


# macOS does not support several TCP_ options
# so check if socket package includes TCP options before adding it
if (_TCP_KEEPIDLE := getattr(socket, "TCP_KEEPIDLE", None)) is not None:
    _keepalive_options[_TCP_KEEPIDLE] = 20

if (_TCP_KEEPINTVL := getattr(socket, "TCP_KEEPINTVL", None)) is not None:
    _keepalive_options[_TCP_KEEPINTVL] = 5

if (_TCP_KEEPCNT := getattr(socket, "TCP_KEEPCNT", None)) is not None:
    _keepalive_options[_TCP_KEEPCNT] = 3


class Ellipsis(object):
    pass


class RedisError(RuntimeError):
    pass


ellipsis: Final[Ellipsis] = Ellipsis()
log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

BUF_SIZE: Final[int] = 1 * 1024 * 1024


class RedisClient(aobject):
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    verbose: bool

    _prev_buf: bytes

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        verbose=False,
    ) -> None:
        self.reader = reader
        self.writer = writer

        self.verbose = verbose

    async def execute(
        self,
        command: Sequence[str | int | float | bytes | memoryview],
        *,
        command_timeout: float | None = None,
    ) -> Any:
        return (
            await self._send(
                [command],
                command_timeout=command_timeout,
            )
        )[0]

    async def pipeline(
        self,
        commands: Sequence[Sequence[str | int | float | bytes | memoryview]],
        *,
        command_timeout: float | None = None,
        return_exception=False,
    ) -> Any:
        return await self._send(
            commands,
            command_timeout=command_timeout,
            return_exception=return_exception,
        )

    async def _send(
        self,
        commands: Sequence[Sequence[str | int | float | bytes | memoryview]],
        *,
        command_timeout: float | None = None,
        return_exception=False,
    ) -> list[Any]:
        """
        Executes a function that issues Redis commands or returns a pipeline/transaction of commands,
        with automatic retries upon temporary connection failures.

        Note that when retried, the given function may be executed *multiple* times, so the caller
        should take care of side-effects of it.
        """

        if command_timeout:
            _timeout_secs = command_timeout
        else:
            _timeout_secs = 10.0

        while True:
            try:
                hiredis_reader = hiredis.Reader(notEnoughData=ellipsis)
                _blobs = bytes()
                for command in commands:
                    request_blob = hiredis.pack_command(tuple(command))  # type: ignore[arg-type]
                    self.writer.write(request_blob)
                    _blobs += request_blob
                async with asyncio.timeout(_timeout_secs):
                    await self.writer.drain()

                if self.verbose:
                    log.debug("requests: {}", commands)
                    log.debug("raw request: {}", _blobs)

                results = []
                first_result = ellipsis

                _buf = bytes()

                met_unexpected_eof = False

                try:
                    while first_result == ellipsis:
                        async with asyncio.timeout(_timeout_secs):
                            buf = await self.reader.read(n=BUF_SIZE)
                        _buf += buf
                        hiredis_reader.feed(buf)
                        first_result = hiredis_reader.gets()
                        if first_result == ellipsis and self.reader.at_eof():
                            met_unexpected_eof = True
                            break
                except hiredis.ProtocolError:
                    raise

                if met_unexpected_eof:
                    log.warning("Met unexpected EOF")
                    raise EOFError

                if self.verbose:
                    log.debug("raw response: {}", _buf)

                if isinstance(first_result, hiredis.HiredisError):
                    if not return_exception:
                        raise first_result
                results.append(first_result)

                while hiredis_reader.has_data():
                    next_result = hiredis_reader.gets()
                    if isinstance(next_result, hiredis.HiredisError):
                        if not return_exception:
                            raise next_result
                    results.append(next_result)

                try:
                    if not len(results) == len(commands):
                        log.warn("requests: {}", commands)
                        log.warn("responses: {}", results)
                        log.warn("raw request: {}", _blobs)
                        log.warn("raw response: {}", _buf)
                        log.warn("previous raw response: {}", self._prev_buf)
                        if _buf.startswith(self._prev_buf):
                            log.warn(
                                "new response contains data of previous response, without it the response should formed like:"
                            )
                            log.warn("{}", _buf[len(self._prev_buf) :])
                        raise RedisError("Response count does not match with number of requests!")
                finally:
                    self._prev_buf = _buf

                if self.verbose:
                    for request, response in zip(commands, results):
                        log.debug("{} -> {}", request, response)

                return results
            except asyncio.CancelledError:
                raise
            finally:
                await asyncio.sleep(0)


class RedisConnection(AsyncContextManager[RedisClient]):
    redis_config: EtcdRedisConfig
    db: int

    socket_timeout: float | None
    socket_connect_timeout: float | None

    def __init__(
        self,
        redis_config: EtcdRedisConfig,
        *,
        db: int = 0,
        socket_timeout: float | None = 5.0,
        socket_connect_timeout: float | None = 2.0,
        keepalive_options: dict[int, int] = _keepalive_options,
    ) -> None:
        self.redis_config = redis_config
        self.db = db
        self.hiredis_reader = hiredis.Reader()

        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.keepalive_options = keepalive_options

    async def connect(self) -> RedisClient:
        if self.redis_config.get("sentinel"):
            raise RuntimeError("Redis with sentinel not supported for this library")

        redis_url = self.redis_config.get("addr")
        assert redis_url is not None

        host = str(redis_url[0])
        port = redis_url[1]
        password = self.redis_config.get("password")

        async with asyncio.timeout(self.socket_connect_timeout):
            reader, writer = await asyncio.open_connection(host, port)
            sock: socket.socket = writer.get_extra_info("socket")
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)

            for opt, val in self.keepalive_options.items():
                sock.setsockopt(socket.IPPROTO_TCP, opt, val)

        self.writer = writer
        self.reader = reader

        client = RedisClient(reader, writer)

        if password:
            await client.execute(
                ["AUTH", password],
                command_timeout=self.socket_timeout,
            )

        await client.execute(
            ["HELLO", "3"],
            command_timeout=self.socket_timeout,
        )
        await client.execute(
            ["SELECT", self.db],
            command_timeout=self.socket_timeout,
        )

        return client

    async def __aenter__(self) -> RedisClient:
        return await self.connect()

    async def disconnect(self) -> None:
        if self.writer:
            try:
                self.writer.close()
            except RuntimeError as e:
                if str(e) == "Event loop is closed":
                    pass  # there's no more room we can do anything
                raise e

    async def __aexit__(self, *exc_info) -> None:
        return await self.disconnect()

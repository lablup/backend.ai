import asyncio
import logging
import time
from typing import Any, AsyncContextManager, Final, Sequence

import async_timeout
import hiredis

from .logging import BraceStyleAdapter
from .types import EtcdRedisConfig, aobject

__all__ = (
    "RedisClient",
    "RedisConnection",
)


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
        reconnect_poll_interval: float | None = None,
        command_timeout: float | None = None,
    ) -> Any:
        return (
            await self._send(
                [command],
                reconnect_poll_interval=reconnect_poll_interval,
                command_timeout=command_timeout,
            )
        )[0]

    async def pipeline(
        self,
        commands: Sequence[Sequence[str | int | float | bytes | memoryview]],
        *,
        reconnect_poll_interval: float | None = None,
        command_timeout: float | None = None,
        return_exception=False,
    ) -> Any:
        return await self._send(
            commands,
            reconnect_poll_interval=reconnect_poll_interval,
            command_timeout=command_timeout,
            return_exception=return_exception,
        )

    async def _send(
        self,
        commands: Sequence[Sequence[str | int | float | bytes | memoryview]],
        *,
        reconnect_poll_interval: float | None = None,
        command_timeout: float | None = None,
        return_exception=False,
    ) -> list[Any]:
        """
        Executes a function that issues Redis commands or returns a pipeline/transaction of commands,
        with automatic retries upon temporary connection failures.

        Note that when retried, the given function may be executed *multiple* times, so the caller
        should take care of side-effects of it.
        """

        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        def show_retry_warning(e: Exception, warn_on_first_attempt: bool = True) -> None:
            nonlocal retry_log_count, last_log_time
            now = time.perf_counter()
            if (warn_on_first_attempt and retry_log_count == 0) or now - last_log_time >= 10.0:
                log.warning(
                    "Retrying due to interruption of Redis connection "
                    "({}, retrying-for: {:.3f}s)",
                    repr(e),
                    now - first_trial,
                )
                retry_log_count += 1
                last_log_time = now

        while True:
            try:
                hiredis_reader = hiredis.Reader(notEnoughData=ellipsis)
                _blobs = bytes()
                for command in commands:
                    request_blob = hiredis.pack_command(tuple(command))  # type: ignore[arg-type]
                    self.writer.write(request_blob)
                    _blobs += request_blob
                await self.writer.drain()

                if self.verbose:
                    log.debug("requests: {}", commands)
                    log.debug("raw request: {}", _blobs)

                results = []
                first_result = ellipsis

                _buf = bytes()
                try:
                    while first_result == ellipsis:
                        buf = await self.reader.read(n=BUF_SIZE)
                        _buf += buf
                        hiredis_reader.feed(buf)
                        first_result = hiredis_reader.gets()
                except hiredis.ProtocolError:
                    raise

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
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    show_retry_warning(e)
                    if reconnect_poll_interval:
                        await asyncio.sleep(reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    show_retry_warning(e)
                    if reconnect_poll_interval:
                        await asyncio.sleep(reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                if command_timeout is not None:
                    now = time.perf_counter()
                    if now - first_trial >= command_timeout + 1.0:
                        show_retry_warning(e)
                continue
            except ConnectionResetError as e:
                show_retry_warning(e)
                if reconnect_poll_interval:
                    await asyncio.sleep(reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            finally:
                await asyncio.sleep(0)


class RedisConnection(AsyncContextManager[RedisClient]):
    redis_config: EtcdRedisConfig
    db: int

    socket_connect_timeout: float | None
    reconnect_poll_timeout: float | None

    def __init__(
        self,
        redis_config: EtcdRedisConfig,
        *,
        db: int = 0,
        socket_connect_timeout: float | None = 2.0,
        reconnect_poll_timeout: float | None = 0.3,
    ) -> None:
        self.redis_config = redis_config
        self.db = db
        self.hiredis_reader = hiredis.Reader()

        self.socket_connect_timeout = socket_connect_timeout
        self.reconnect_poll_timeout = reconnect_poll_timeout

    async def connect(self) -> RedisClient:
        if self.redis_config.get("sentinel"):
            raise RuntimeError("Redis with sentinel not supported for this library")

        redis_url = self.redis_config.get("addr")
        assert redis_url is not None

        host = str(redis_url[0])
        port = redis_url[1]
        password = self.redis_config.get("password")

        async with async_timeout.timeout(self.socket_connect_timeout):
            reader, writer = await asyncio.open_connection(host, port)

        self.writer = writer
        self.reader = reader

        client = RedisClient(reader, writer)

        if password:
            await client.execute(
                ["AUTH", password], reconnect_poll_interval=self.reconnect_poll_timeout
            )

        await client.execute(["HELLO", "3"], reconnect_poll_interval=self.reconnect_poll_timeout)
        await client.execute(
            ["SELECT", self.db], reconnect_poll_interval=self.reconnect_poll_timeout
        )

        return client

    async def __aenter__(self) -> RedisClient:
        return await self.connect()

    async def disconnect(self) -> None:
        self.writer.close()

    async def __aexit__(self, *exc_info) -> None:
        return await self.disconnect()

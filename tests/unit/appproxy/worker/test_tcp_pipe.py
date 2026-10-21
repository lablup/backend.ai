from __future__ import annotations

import asyncio
import errno
import gc
import logging
import sys
import weakref
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from functools import partial
from types import TracebackType
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.proxy.backend.tcp import TCPBackend
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo

PORT = 10201
USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
TIMEOUT = 5.0


def _create_circuit(kernel_port: int) -> Circuit:
    return Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="jupyter",
        protocol=ProxyProtocol.TCP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(PORT),
        port=PORT,
        app_info=InteractiveAppInfo(user_id=USER_ID),
        subdomain=None,
        runtime_variant=None,
        envs={},
        arguments=None,
        open_to_public=True,
        allowed_client_ips=None,
        user_id=USER_ID,
        access_key="AKIAIOSFODNN7EXAMPLE",
        endpoint_id=None,
        route_info=[
            RouteInfo(
                route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=kernel_port,
                protocol=ProxyProtocol.TCP,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452, tzinfo=UTC),
    )


class _Upstream:
    """A localhost upstream whose per-connection handler is supplied by the test."""

    port: int
    _server: asyncio.Server

    def __init__(self, server: asyncio.Server) -> None:
        self._server = server
        self.port = server.sockets[0].getsockname()[1]


class _UnraisableCollector:
    unraisable: list[Any]
    _prev: Callable[[Any], object]

    def __init__(self) -> None:
        self.unraisable = []

    def __enter__(self) -> _UnraisableCollector:
        self._prev = sys.unraisablehook
        sys.unraisablehook = self.unraisable.append
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        sys.unraisablehook = self._prev


@pytest.fixture
def root_context() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.last_used_time_marker_redis_queue = asyncio.Queue()
    root_ctx.request_counter_redis_queue = asyncio.Queue()
    return root_ctx


async def _start_upstream(
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Any],
) -> _Upstream:
    return _Upstream(await asyncio.start_server(handler, "127.0.0.1", 0))


@pytest.fixture
async def servers() -> AsyncIterator[list[asyncio.Server]]:
    started: list[asyncio.Server] = []
    try:
        yield started
    finally:
        for server in started:
            server.close()
            await server.wait_closed()


class TestTCPPipe:
    async def test_abandoned_half_closed_pipe_survives_gc(
        self,
        root_context: MagicMock,
        servers: list[asyncio.Server],
    ) -> None:
        upstream_accepted = asyncio.Event()
        upstream_writers: list[asyncio.StreamWriter] = []
        conn_task_refs: list[weakref.ref[asyncio.Task[Any]]] = []

        async def idle_upstream(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            upstream_writers.append(w)
            upstream_accepted.set()
            await r.read()

        upstream = await _start_upstream(idle_upstream)
        servers.append(upstream._server)
        circuit = _create_circuit(upstream.port)
        frontend = TCPFrontend(root_context)
        frontend.circuits[PORT] = circuit
        frontend.backends[PORT] = TCPBackend(circuit.route_info, root_context, circuit)

        async def pipe_handler(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            task = asyncio.current_task()
            assert task is not None
            conn_task_refs.append(weakref.ref(task))
            del task
            await frontend.pipe(PORT, r, w)

        proxy = await asyncio.start_server(pipe_handler, "127.0.0.1", 0)
        servers.append(proxy)
        proxy_port: int = proxy.sockets[0].getsockname()[1]

        try:
            _, client_w = await asyncio.open_connection("127.0.0.1", proxy_port)
            await asyncio.wait_for(upstream_accepted.wait(), TIMEOUT)
            client_w.write_eof()
            await asyncio.sleep(0.05)
            conn_task_ref = conn_task_refs[0]
            loop_errors: list[str] = []
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(lambda _loop, ctx: loop_errors.append(ctx["message"]))

            try:
                with _UnraisableCollector() as collector:
                    for _ in range(3):
                        gc.collect()
                        await asyncio.sleep(0)
            finally:
                loop.set_exception_handler(None)

            assert collector.unraisable == []
            assert loop_errors == []
            conn_task = conn_task_ref()
            assert conn_task is not None
            assert not conn_task.done()
            del conn_task
            client_w.close()
        finally:
            for w in upstream_writers:
                w.close()
            await frontend.stop()
            await frontend.backends[PORT].close()

    async def test_half_close_propagates_and_reply_still_flows(
        self,
        root_context: MagicMock,
        servers: list[asyncio.Server],
    ) -> None:
        upstream_saw: list[bytes] = []

        async def echo_after_eof(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            upstream_saw.append(await r.read())  # returns only on EOF
            w.write(b"reply-after-eof")
            await w.drain()
            w.close()

        upstream = await _start_upstream(echo_after_eof)
        servers.append(upstream._server)
        circuit = _create_circuit(upstream.port)
        backend = TCPBackend(circuit.route_info, root_context, circuit)
        proxy = await asyncio.start_server(backend.bind, "127.0.0.1", 0)
        servers.append(proxy)
        proxy_port: int = proxy.sockets[0].getsockname()[1]

        try:
            client_r, client_w = await asyncio.open_connection("127.0.0.1", proxy_port)
            client_w.write(b"request")
            client_w.write_eof()
            reply = await asyncio.wait_for(client_r.read(), TIMEOUT)
            client_w.close()
        finally:
            await backend.close()

        assert upstream_saw == [b"request"]
        assert reply == b"reply-after-eof"

    async def test_runtime_error_from_write_ends_direction_without_exception_group(
        self,
        root_context: MagicMock,
        servers: list[asyncio.Server],
    ) -> None:
        async def send_then_wait(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            w.write(b"data")
            await w.drain()
            await r.read()
            w.close()

        upstream = await _start_upstream(send_then_wait)
        servers.append(upstream._server)
        circuit = _create_circuit(upstream.port)
        backend = TCPBackend(circuit.route_info, root_context, circuit)

        down_writer = MagicMock()
        down_writer.write.side_effect = RuntimeError("unable to perform operation on handle")
        down_writer.can_write_eof.return_value = True
        down_writer.drain = AsyncMock()
        down_writer.wait_closed = AsyncMock()
        down_reader = asyncio.StreamReader()
        down_reader.feed_eof()

        try:
            await asyncio.wait_for(backend.bind(down_reader, down_writer), TIMEOUT)
        finally:
            await backend.close()

        down_writer.write.assert_called_once_with(b"data")

    @pytest.mark.parametrize(
        "error",
        [
            OSError(errno.ENOTCONN, "Transport endpoint is not connected"),
            ConnectionResetError(errno.ECONNRESET, "Connection reset by peer"),
        ],
    )
    async def test_client_gone_before_close_is_a_normal_end(
        self,
        error: OSError,
        root_context: MagicMock,
        servers: list[asyncio.Server],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        async def idle_upstream(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            await r.read()
            w.close()

        upstream = await _start_upstream(idle_upstream)
        servers.append(upstream._server)
        circuit = _create_circuit(upstream.port)
        frontend = TCPFrontend(root_context)
        frontend.circuits[PORT] = circuit
        frontend.backends[PORT] = TCPBackend(circuit.route_info, root_context, circuit)

        down_writer = MagicMock()
        down_writer.can_write_eof.return_value = True
        down_writer.drain = AsyncMock()
        down_writer.wait_closed = AsyncMock(side_effect=error)
        down_reader = asyncio.StreamReader()
        down_reader.feed_eof()

        try:
            with caplog.at_level(logging.DEBUG):
                await asyncio.wait_for(frontend.pipe(PORT, down_reader, down_writer), TIMEOUT)
        finally:
            await frontend.backends[PORT].close()

        down_writer.wait_closed.assert_awaited_once()
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []

    @pytest.mark.parametrize("reject", ["no_backend", "peer_not_allowed"])
    async def test_client_reset_on_reject_path_is_a_normal_end(
        self,
        reject: str,
        root_context: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        circuit = _create_circuit(1)
        frontend = TCPFrontend(root_context)
        frontend.circuits[PORT] = circuit
        backend = MagicMock()
        backend.circuit.ip_validator.is_restricted = True
        backend.circuit.ip_validator.is_allowed.return_value = False
        if reject == "peer_not_allowed":
            frontend.backends[PORT] = backend

        writer = MagicMock()
        writer.get_extra_info.return_value = ("10.0.0.1", 12345)
        writer.wait_closed = AsyncMock(
            side_effect=ConnectionResetError(errno.ECONNRESET, "Connection reset by peer")
        )

        with caplog.at_level(logging.DEBUG):
            await asyncio.wait_for(frontend.pipe(PORT, asyncio.StreamReader(), writer), TIMEOUT)

        if reject == "peer_not_allowed":
            backend.circuit.ip_validator.is_allowed.assert_called_once_with("10.0.0.1")
        writer.close.assert_called_once()
        writer.wait_closed.assert_awaited_once()
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []

    async def test_stop_returns_with_open_half_closed_connection(
        self,
        root_context: MagicMock,
        servers: list[asyncio.Server],
    ) -> None:
        upstream_accepted = asyncio.Event()
        upstream_writers: list[asyncio.StreamWriter] = []

        async def idle_upstream(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            upstream_writers.append(w)
            upstream_accepted.set()
            await r.read()

        upstream = await _start_upstream(idle_upstream)
        servers.append(upstream._server)
        circuit = _create_circuit(upstream.port)
        frontend = TCPFrontend(root_context)
        frontend.circuits[PORT] = circuit
        frontend.backends[PORT] = TCPBackend(circuit.route_info, root_context, circuit)
        proxy = await asyncio.start_server(partial(frontend.pipe, PORT), "127.0.0.1", 0)
        frontend.servers.append(proxy)
        proxy_port: int = proxy.sockets[0].getsockname()[1]

        try:
            _, client_w = await asyncio.open_connection("127.0.0.1", proxy_port)
            await asyncio.wait_for(upstream_accepted.wait(), TIMEOUT)
            client_w.write_eof()
            await asyncio.sleep(0.05)
            assert len(frontend._conn_tasks) == 1

            await asyncio.wait_for(frontend.stop(), TIMEOUT)
            client_w.close()
        finally:
            for w in upstream_writers:
                w.close()
            await frontend.backends[PORT].close()
        assert frontend._conn_tasks == set()

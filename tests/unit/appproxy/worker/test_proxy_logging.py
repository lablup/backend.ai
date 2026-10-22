from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import aiohttp
import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors import ContainerConnectionRefused
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend
from ai.backend.appproxy.worker.proxy.backend.tcp import TCPBackend
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo

WORKER_LOGGER_NAME = "ai.backend.appproxy.worker"
TRACE_LEVEL = 5
PORT = 10200
CIRCUIT_ID = UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372")


def _closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


def _create_circuit(protocol: ProxyProtocol, kernel_port: int) -> Circuit:
    return Circuit(
        id=CIRCUIT_ID,
        app="jupyter",
        protocol=protocol,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(PORT),
        port=PORT,
        app_info=InteractiveAppInfo(user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")),
        subdomain=None,
        runtime_variant=None,
        envs={},
        arguments=None,
        open_to_public=True,
        allowed_client_ips=None,
        user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        access_key="AKIAIOSFODNN7EXAMPLE",
        endpoint_id=None,
        route_info=[
            RouteInfo(
                route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=kernel_port,
                protocol=protocol,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452, tzinfo=UTC),
    )


def _worker_records(caplog: pytest.LogCaptureFixture, min_level: int) -> list[logging.LogRecord]:
    return [
        record
        for record in caplog.records
        if record.name.startswith(WORKER_LOGGER_NAME) and record.levelno >= min_level
    ]


@pytest.fixture
def root_context() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.last_used_time_marker_redis_queue = asyncio.Queue()
    root_ctx.request_counter_redis_queue = asyncio.Queue()
    return root_ctx


class TestHTTPProxyLogging:
    @pytest.fixture
    async def http_frontend(
        self,
        mocker: pytest_mock.MockerFixture,
        root_context: MagicMock,
    ) -> AsyncIterator[PortFrontend]:
        mocker.patch(
            "ai.backend.appproxy.worker.proxy.backend.http.ClientPool",
            return_value=mocker.MagicMock(close=mocker.AsyncMock()),
        )
        root_context.local_config.proxy_worker.trusted_proxies = []
        frontend = PortFrontend(root_context)
        circuit = _create_circuit(ProxyProtocol.HTTP, kernel_port=_closed_port())
        backend = HTTPBackend(circuit.route_info, root_context, circuit)
        frontend.circuits[PORT] = circuit
        frontend.backends[PORT] = backend
        try:
            yield frontend
        finally:
            await backend.close()

    def _request(self) -> web.Request:
        app = web.Application()
        app["port"] = PORT
        return make_mocked_request(method="GET", path="/", headers={}, app=app)

    async def test_internal_exception_logs_one_error_with_circuit_id(
        self,
        mocker: pytest_mock.MockerFixture,
        http_frontend: PortFrontend,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mocker.patch.object(
            http_frontend.backends[PORT], "request_http", side_effect=RuntimeError("boom")
        )

        with caplog.at_level(TRACE_LEVEL, logger=WORKER_LOGGER_NAME):
            with pytest.raises(RuntimeError):
                await http_frontend.ensure_slot_middleware(self._request(), http_frontend.proxy)

        errors = _worker_records(caplog, logging.ERROR)
        assert len(errors) == 1
        assert errors[0].__dict__["log_tag_circuit_id"] == str(CIRCUIT_ID)
        assert errors[0].exc_info is not None

    async def test_refused_app_connection_logs_nothing_at_info_or_above(
        self,
        mocker: pytest_mock.MockerFixture,
        http_frontend: PortFrontend,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mocker.patch.object(
            http_frontend.backends[PORT],
            "request_http",
            side_effect=aiohttp.ClientOSError(111, "Connection refused"),
        )

        with caplog.at_level(TRACE_LEVEL, logger=WORKER_LOGGER_NAME):
            with pytest.raises(ContainerConnectionRefused):
                await http_frontend.ensure_slot_middleware(self._request(), http_frontend.proxy)

        assert _worker_records(caplog, logging.INFO) == []
        traces = [
            record
            for record in _worker_records(caplog, TRACE_LEVEL)
            if record.levelno == TRACE_LEVEL
            and record.getMessage().startswith("app refused the connection")
        ]
        assert len(traces) == 1
        assert traces[0].__dict__["log_tag_circuit_id"] == str(CIRCUIT_ID)


class TestTCPProxyLogging:
    @pytest.fixture
    async def tcp_frontend(
        self,
        root_context: MagicMock,
    ) -> AsyncIterator[TCPFrontend]:
        frontend = TCPFrontend(root_context)
        circuit = _create_circuit(ProxyProtocol.TCP, kernel_port=_closed_port())
        backend = TCPBackend(circuit.route_info, root_context, circuit)
        frontend.circuits[PORT] = circuit
        frontend.backends[PORT] = backend
        try:
            yield frontend
        finally:
            await backend.close()

    def _writer(self) -> MagicMock:
        writer = MagicMock()
        writer.get_extra_info.return_value = ("127.0.0.1", 54321)
        writer.wait_closed = AsyncMock()
        return writer

    async def test_refused_app_connection_logs_nothing_at_info_or_above(
        self,
        mocker: pytest_mock.MockerFixture,
        tcp_frontend: TCPFrontend,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        writer = self._writer()

        with caplog.at_level(TRACE_LEVEL, logger=WORKER_LOGGER_NAME):
            await tcp_frontend.pipe(PORT, mocker.MagicMock(), writer)

        assert _worker_records(caplog, logging.INFO) == []
        writer.close.assert_called_once()

    async def test_internal_exception_logs_one_error_with_circuit_id(
        self,
        mocker: pytest_mock.MockerFixture,
        tcp_frontend: TCPFrontend,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mocker.patch.object(tcp_frontend.backends[PORT], "bind", side_effect=RuntimeError("boom"))

        with caplog.at_level(TRACE_LEVEL, logger=WORKER_LOGGER_NAME):
            await tcp_frontend.pipe(PORT, mocker.MagicMock(), self._writer())

        errors = _worker_records(caplog, logging.ERROR)
        assert len(errors) == 1
        assert errors[0].__dict__["log_tag_circuit_id"] == str(CIRCUIT_ID)
        assert errors[0].exc_info is not None

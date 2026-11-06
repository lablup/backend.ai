from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import aiomonitor
import pytest
from aiohttp import web

from ai.backend.appproxy.common.events import (
    AppProxyCircuitCreatedEvent,
    AppProxyWorkerCircuitAddedEvent,
)
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    SerializableCircuit,
)
from ai.backend.appproxy.worker import server
from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend
from ai.backend.common.types import AgentId

_WORKER_AUTHORITY = "worker-1"
_LISTEN_PORT = 10200
_API_PORT = 20000
_USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")


@dataclass(frozen=True)
class _H2WorkerAndPrivateCircuitToRegister:
    root_context: MagicMock
    private_circuit_to_register: SerializableCircuit


@pytest.fixture
def h2_worker_and_private_circuit_to_register() -> _H2WorkerAndPrivateCircuitToRegister:
    root_context = MagicMock()
    root_context.local_config.proxy_worker.authority = _WORKER_AUTHORITY
    root_context.local_config.proxy_worker.http2.api_port_pool = (_API_PORT, _API_PORT)
    root_context.event_producer.broadcast_event = AsyncMock()
    root_context.proxy_frontend = PortFrontend(root_context)
    private_circuit_to_register = SerializableCircuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="grpc-app",
        protocol=ProxyProtocol.HTTP2,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        envs={},
        arguments=None,
        open_to_public=False,
        allowed_client_ips=None,
        port=_LISTEN_PORT,
        subdomain=None,
        user_id=_USER_ID,
        endpoint_id=None,
        runtime_variant=None,
        route_info=[],
        session_ids=[],
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return _H2WorkerAndPrivateCircuitToRegister(root_context, private_circuit_to_register)


class TestHandleProxyRouteEvent:
    async def test_created_event_acknowledges_a_skipped_circuit_to_the_coordinator(
        self,
        h2_worker_and_private_circuit_to_register: _H2WorkerAndPrivateCircuitToRegister,
    ) -> None:
        private_circuit = h2_worker_and_private_circuit_to_register.private_circuit_to_register

        await server.handle_proxy_route_event(
            h2_worker_and_private_circuit_to_register.root_context,
            AgentId("manager"),
            AppProxyCircuitCreatedEvent(
                target_worker_authority=_WORKER_AUTHORITY,
                circuits=[private_circuit],
            ),
        )

        broadcast_event = (
            h2_worker_and_private_circuit_to_register.root_context.event_producer.broadcast_event
        )
        broadcast_event.assert_awaited_once_with(
            AppProxyWorkerCircuitAddedEvent(
                target_worker_authority=_WORKER_AUTHORITY,
                circuits=[private_circuit],
            )
        )


@pytest.fixture
def monitor_start() -> Iterator[MagicMock]:
    with (
        patch.object(aiomonitor.Monitor, "start", autospec=True) as start,
        patch.object(aiomonitor.Monitor, "close", autospec=True),
    ):
        yield start


@pytest.fixture
def webapp_stubs() -> Iterator[None]:
    with (
        patch.object(server, "build_root_app", MagicMock()),
        patch.object(web, "AppRunner", return_value=AsyncMock()),
        patch.object(web, "TCPSite", return_value=AsyncMock()),
        patch.object(os, "geteuid", return_value=1000),
    ):
        yield


@pytest.mark.usefixtures("webapp_stubs")
async def test_server_main_opens_aiomonitor_on_localhost(monitor_start: MagicMock) -> None:
    local_config = MagicMock()
    local_config.debug.enhanced_aiomonitor_task_info = False
    local_config.proxy_worker.tls_listen = False
    local_config.proxy_worker.aiomonitor_termui_port = 48600
    local_config.proxy_worker.aiomonitor_webui_port = 49600

    async with server.server_main(asyncio.get_running_loop(), 0, [local_config]):
        pass

    monitor_start.assert_called_once()
    monitor: aiomonitor.Monitor = monitor_start.call_args.args[0]
    assert monitor.host == "127.0.0.1"

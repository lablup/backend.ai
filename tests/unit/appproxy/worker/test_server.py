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
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend
from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressFrontendKey
from ai.backend.common.types import AgentId

_WORKER_AUTHORITY = "worker-1"
_LISTEN_PORT = 10200
_API_PORT = 20000
_LISTEN_PORT_INGRESS_KEY = IngressFrontendKey(f"port-{_LISTEN_PORT}")
_USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")


@dataclass(frozen=True)
class _CircuitAccessCase:
    open_to_public: bool
    allowed_client_ips: str | None
    expected_ingress_keys: list[IngressFrontendKey]


@dataclass(frozen=True)
class _H2WorkerAndCircuitToRegister:
    root_context: MagicMock
    ingress_state: InMemoryIngressState
    circuit_to_register: SerializableCircuit


@pytest.fixture
def h2_worker_and_circuit_to_register(
    case: _CircuitAccessCase,
) -> Iterator[_H2WorkerAndCircuitToRegister]:
    root_context = MagicMock()
    root_context.local_config.proxy_worker.authority = _WORKER_AUTHORITY
    root_context.local_config.proxy_worker.http2.api_port_pool = (_API_PORT, _API_PORT)
    root_context.event_producer.broadcast_event = AsyncMock()
    ingress_state = InMemoryIngressState()
    root_context.ingress_state.writer = ValidatingIngressWriter(
        ingress_state, IngressAuthority(_WORKER_AUTHORITY)
    )
    h2_frontend = PortFrontend(root_context)
    h2_frontend.api_ports = {_LISTEN_PORT: _API_PORT}
    root_context.proxy_frontend = h2_frontend
    circuit_to_register = SerializableCircuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="grpc-app",
        protocol=ProxyProtocol.HTTP2,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        envs={},
        arguments=None,
        open_to_public=case.open_to_public,
        allowed_client_ips=case.allowed_client_ips,
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
    with patch.object(H2Backend, "update_config", AsyncMock()):
        yield _H2WorkerAndCircuitToRegister(root_context, ingress_state, circuit_to_register)


class TestWorkerRegistrationCtx:
    @pytest.fixture
    def coordinator_listing_the_circuit(
        self, h2_worker_and_circuit_to_register: _H2WorkerAndCircuitToRegister
    ) -> Iterator[None]:
        listed_circuit = Circuit.from_serialized_circuit(
            h2_worker_and_circuit_to_register.circuit_to_register
        )
        with (
            patch.object(server, "register_worker", AsyncMock()),
            patch.object(server, "deregister_worker", AsyncMock()),
            patch.object(server, "list_worker_circuits", AsyncMock(return_value=[listed_circuit])),
            patch.object(server, "WorkerHeartbeatTask"),
            patch.object(server, "LocalCron", return_value=AsyncMock()),
        ):
            yield

    @pytest.mark.usefixtures("coordinator_listing_the_circuit")
    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=True,
                    allowed_client_ips=None,
                    expected_ingress_keys=[_LISTEN_PORT_INGRESS_KEY],
                ),
                id="public_without_allowlist_is_recorded",
            ),
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=False,
                    allowed_client_ips=None,
                    expected_ingress_keys=[],
                ),
                id="private_is_not_recorded",
            ),
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=True,
                    allowed_client_ips="10.0.0.0/8",
                    expected_ingress_keys=[],
                ),
                id="public_with_allowlist_is_not_recorded",
            ),
        ],
    )
    async def test_ingress_state_holds_only_the_registered_circuit(
        self,
        case: _CircuitAccessCase,
        h2_worker_and_circuit_to_register: _H2WorkerAndCircuitToRegister,
    ) -> None:
        async with server.worker_registration_ctx(h2_worker_and_circuit_to_register.root_context):
            recorded_ingresses = await h2_worker_and_circuit_to_register.ingress_state.get_all()

        assert [
            ingress.frontend.key() for ingress in recorded_ingresses
        ] == case.expected_ingress_keys


class TestHandleProxyRouteEvent:
    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=True,
                    allowed_client_ips=None,
                    expected_ingress_keys=[_LISTEN_PORT_INGRESS_KEY],
                ),
                id="public_without_allowlist_is_recorded",
            ),
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=False,
                    allowed_client_ips=None,
                    expected_ingress_keys=[],
                ),
                id="private_is_not_recorded",
            ),
            pytest.param(
                _CircuitAccessCase(
                    open_to_public=True,
                    allowed_client_ips="10.0.0.0/8",
                    expected_ingress_keys=[],
                ),
                id="public_with_allowlist_is_not_recorded",
            ),
        ],
    )
    async def test_created_event_records_only_the_registered_circuit(
        self,
        case: _CircuitAccessCase,
        h2_worker_and_circuit_to_register: _H2WorkerAndCircuitToRegister,
    ) -> None:
        await server.handle_proxy_route_event(
            h2_worker_and_circuit_to_register.root_context,
            AgentId("manager"),
            AppProxyCircuitCreatedEvent(
                target_worker_authority=_WORKER_AUTHORITY,
                circuits=[h2_worker_and_circuit_to_register.circuit_to_register],
            ),
        )

        recorded_ingresses = await h2_worker_and_circuit_to_register.ingress_state.get_all()
        assert [
            ingress.frontend.key() for ingress in recorded_ingresses
        ] == case.expected_ingress_keys

    @pytest.mark.parametrize(
        "case",
        [
            _CircuitAccessCase(
                open_to_public=False,
                allowed_client_ips=None,
                expected_ingress_keys=[],
            ),
        ],
    )
    async def test_created_event_acknowledges_a_skipped_circuit_to_the_coordinator(
        self,
        case: _CircuitAccessCase,
        h2_worker_and_circuit_to_register: _H2WorkerAndCircuitToRegister,
    ) -> None:
        circuit_to_register = h2_worker_and_circuit_to_register.circuit_to_register

        await server.handle_proxy_route_event(
            h2_worker_and_circuit_to_register.root_context,
            AgentId("manager"),
            AppProxyCircuitCreatedEvent(
                target_worker_authority=_WORKER_AUTHORITY,
                circuits=[circuit_to_register],
            ),
        )

        broadcast_event = (
            h2_worker_and_circuit_to_register.root_context.event_producer.broadcast_event
        )
        broadcast_event.assert_awaited_once_with(
            AppProxyWorkerCircuitAddedEvent(
                target_worker_authority=_WORKER_AUTHORITY,
                circuits=[circuit_to_register],
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

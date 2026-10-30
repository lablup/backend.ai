from __future__ import annotations

import gzip
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from ipaddress import ip_network
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import aiohttp
import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors import ClientIPNotAllowed, GenericBadRequest
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit, InferenceAppInfo, PortFrontendInfo
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority
from ai.backend.common.types import RuntimeVariant

_AUTHORITY = IngressAuthority("worker-1")
_PORT = 10200
_GZIP_REQUEST_BODY = gzip.compress(b'{"data": "' + b"a" * 1000 + b'"}')


def create_circuit(port: int) -> Circuit:
    return Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="vllm",
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(port),
        port=port,
        app_info=InferenceAppInfo(
            endpoint_id=UUID("b9567a3b-3ca1-4d8f-b8eb-a9567073808d"),
            runtime_variant=RuntimeVariant("vllm"),
        ),
        subdomain=None,
        runtime_variant=RuntimeVariant("vllm"),
        envs={},
        arguments=None,
        open_to_public=False,
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
                kernel_port=30729,
                protocol=ProxyProtocol.HTTP,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452, tzinfo=UTC),
    )


class _IngressPresence(StrEnum):
    HELD = "held"
    REMOVED = "removed"
    NEVER_HELD = "never-held"


@dataclass(frozen=True)
class _PortSlotCase:
    name: str
    backend_registered: bool = True
    ingress_presence: _IngressPresence = _IngressPresence.HELD
    allowed_client_ips: list[str] = field(default_factory=list)
    client_ip: str = "10.0.0.1"


@dataclass(frozen=True)
class _PortSlotSituation:
    frontend: PortFrontend
    request: web.Request
    handler: AsyncMock
    backend: MagicMock
    ensure_credential: MagicMock


@pytest.fixture
async def port_slot_situation(
    mocker: pytest_mock.MockerFixture, case: _PortSlotCase
) -> _PortSlotSituation:
    circuit = create_circuit(_PORT)
    circuit_ingress = circuit.to_ingress(_AUTHORITY)
    ingress = circuit_ingress.model_copy(
        update={
            "access": circuit_ingress.access.model_copy(
                update={
                    "allowed_client_ips": [ip_network(cidr) for cidr in case.allowed_client_ips]
                }
            )
        }
    )
    in_memory = InMemoryIngressState(negative_ttl=60.0)
    match case.ingress_presence:
        case _IngressPresence.HELD:
            await in_memory.apply([ingress])
        case _IngressPresence.REMOVED:
            await in_memory.apply([ingress])
            await in_memory.remove([ingress.key()])
        case _IngressPresence.NEVER_HELD:
            pass
    root_context = mocker.MagicMock()
    root_context.ingress_state = IngressState(
        reader=LayeredIngressState([in_memory], in_memory=in_memory), writer=None
    )
    frontend = PortFrontend(root_context=root_context)
    backend = mocker.MagicMock(circuit=circuit)
    if case.backend_registered:
        frontend.backends[_PORT] = backend
    app = web.Application()
    app["port"] = _PORT
    return _PortSlotSituation(
        frontend=frontend,
        request=make_mocked_request(method="GET", path="/", headers={}, app=app).clone(
            remote=case.client_ip
        ),
        handler=mocker.AsyncMock(return_value=web.Response(text="success")),
        backend=backend,
        ensure_credential=mocker.patch.object(frontend, "ensure_credential"),
    )


@dataclass(frozen=True)
class _ServingPortFrontend:
    port: int
    bodies_received_by_backend: list[bytes]


@pytest.fixture
async def serving_port_frontend(
    mocker: pytest_mock.MockerFixture,
    unused_tcp_port: int,
) -> AsyncIterator[_ServingPortFrontend]:
    root_context = mocker.MagicMock()
    proxy_worker_config = root_context.local_config.proxy_worker
    proxy_worker_config.tls_listen = False
    proxy_worker_config.trusted_proxies = []
    proxy_worker_config.max_header_field_size = 8190
    proxy_worker_config.port_proxy.bind_host = "127.0.0.1"
    proxy_worker_config.port_proxy.bind_port_range = (unused_tcp_port, unused_tcp_port)
    bodies_received_by_backend: list[bytes] = []

    async def record_request_body(request: web.Request) -> web.Response:
        bodies_received_by_backend.append(await request.read())
        return web.Response()

    circuit = create_circuit(unused_tcp_port).model_copy(update={"open_to_public": True})
    in_memory = InMemoryIngressState()
    await in_memory.apply([circuit.to_ingress(_AUTHORITY)])
    root_context.ingress_state = IngressState(
        reader=LayeredIngressState([in_memory], in_memory=in_memory), writer=None
    )
    frontend = PortFrontend(root_context=root_context)
    frontend.backends = {
        unused_tcp_port: mocker.MagicMock(proxy_http=record_request_body, circuit=circuit)
    }
    await frontend.start()
    yield _ServingPortFrontend(
        port=unused_tcp_port,
        bodies_received_by_backend=bodies_received_by_backend,
    )
    await frontend.stop()


class TestPortFrontend:
    @pytest.mark.parametrize(
        "case",
        [
            _PortSlotCase(
                name="no-backend",
                backend_registered=False,
                ingress_presence=_IngressPresence.NEVER_HELD,
            ),
            _PortSlotCase(name="ingress-never-held", ingress_presence=_IngressPresence.NEVER_HELD),
            _PortSlotCase(name="ingress-removed", ingress_presence=_IngressPresence.REMOVED),
        ],
        ids=lambda case: case.name,
    )
    async def test_unregistered_slot_is_rejected(
        self, case: _PortSlotCase, port_slot_situation: _PortSlotSituation
    ) -> None:
        situation = port_slot_situation
        with pytest.raises(GenericBadRequest):
            await situation.frontend.ensure_slot_middleware(situation.request, situation.handler)
        situation.handler.assert_not_awaited()

    @pytest.mark.parametrize("case", [_PortSlotCase(name="registered")], ids=lambda case: case.name)
    async def test_registered_slot_reaches_the_handler_with_its_backend(
        self, case: _PortSlotCase, port_slot_situation: _PortSlotSituation
    ) -> None:
        situation = port_slot_situation
        response = await situation.frontend.ensure_slot_middleware(
            situation.request, situation.handler
        )
        assert isinstance(response, web.Response)
        assert response.text == "success"
        assert situation.request["backend"] is situation.backend
        situation.ensure_credential.assert_called_once_with(
            situation.request, situation.backend.circuit
        )

    @pytest.mark.parametrize(
        "case",
        [
            _PortSlotCase(
                name="ipv4-outside", allowed_client_ips=["192.168.0.0/24"], client_ip="10.0.0.1"
            ),
            _PortSlotCase(
                name="ipv6-outside", allowed_client_ips=["fd00::/8"], client_ip="2001:db8::1"
            ),
            _PortSlotCase(
                name="unparsable-remote",
                allowed_client_ips=["192.168.0.0/24"],
                client_ip="not-an-ip",
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_client_outside_the_ingress_allowlist_is_rejected(
        self, case: _PortSlotCase, port_slot_situation: _PortSlotSituation
    ) -> None:
        situation = port_slot_situation
        with pytest.raises(ClientIPNotAllowed):
            await situation.frontend.ensure_slot_middleware(situation.request, situation.handler)
        situation.handler.assert_not_awaited()

    @pytest.mark.parametrize(
        "case",
        [
            _PortSlotCase(
                name="ipv4-inside", allowed_client_ips=["10.0.0.0/8"], client_ip="10.0.0.1"
            ),
            _PortSlotCase(
                name="ipv6-inside", allowed_client_ips=["2001:db8::/32"], client_ip="2001:db8::1"
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_client_inside_the_ingress_allowlist_reaches_the_handler(
        self, case: _PortSlotCase, port_slot_situation: _PortSlotSituation
    ) -> None:
        situation = port_slot_situation
        await situation.frontend.ensure_slot_middleware(situation.request, situation.handler)
        situation.handler.assert_awaited_once()

    async def test_proxy_passes_compressed_request_body_as_received(
        self,
        serving_port_frontend: _ServingPortFrontend,
    ) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://127.0.0.1:{serving_port_frontend.port}/",
                data=_GZIP_REQUEST_BODY,
                headers={"Content-Encoding": "gzip"},
            ) as response:
                assert response.status == 200

        assert serving_port_frontend.bodies_received_by_backend == [_GZIP_REQUEST_BODY]

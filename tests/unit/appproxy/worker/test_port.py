from __future__ import annotations

import gzip
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import aiohttp
import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors import GenericBadRequest
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit, InferenceAppInfo, PortFrontendInfo
from ai.backend.common.types import RuntimeVariant

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


@pytest.fixture
def port_frontend(mocker: pytest_mock.MockerFixture) -> PortFrontend:
    frontend = PortFrontend(root_context=mocker.MagicMock())
    frontend.circuits = {}
    frontend.backends = {}
    return frontend


async def test_ensure_slot_unregistered_port(
    mocker: pytest_mock.MockerFixture,
    port_frontend: PortFrontend,
) -> None:
    """
    Test that a GenericBadRequest is raised for an unregistered port.
    """
    port = 10200
    app = web.Application()
    app.update({"port": port})
    request = make_mocked_request(method="GET", path="/", headers={}, app=app)
    handler = mocker.AsyncMock()

    with pytest.raises(GenericBadRequest):
        await port_frontend.ensure_slot_middleware(request, handler)


async def test_ensure_slot_no_circuit(
    mocker: pytest_mock.MockerFixture,
    port_frontend: PortFrontend,
) -> None:
    """
    Test that a GenericBadRequest is raised when no circuit is available for a registered port.
    """
    port = 10200
    app = web.Application()
    app.update({"port": port})
    request = make_mocked_request(method="GET", path="/", headers={}, app=app)
    handler = mocker.AsyncMock()

    port_frontend.circuits.pop(port, None)  # ensure deleted
    port_frontend.backends.pop(port, None)  # ensure deleted

    with pytest.raises(GenericBadRequest):
        await port_frontend.ensure_slot_middleware(request, handler)


async def test_ensure_slot(
    mocker: pytest_mock.MockerFixture,
    port_frontend: PortFrontend,
) -> None:
    """
    Test the normal flow where a circuit and backend are properly set up.
    """
    port = 10200
    app = web.Application()
    app.update({"port": port})
    request = make_mocked_request(method="GET", path="/", headers={}, app=app)
    handler = mocker.AsyncMock(return_value=web.Response(text="success"))

    circuit = create_circuit(port=port)
    backend = mocker.MagicMock()
    port_frontend.circuits[port] = circuit
    port_frontend.backends[port] = backend

    mocked_ensure_credential = mocker.patch.object(port_frontend, "ensure_credential")

    response = await port_frontend.ensure_slot_middleware(request, handler)
    assert isinstance(response, web.Response)  # for this test case

    assert response.text == "success"
    assert request["circuit"] == circuit
    assert request["backend"] == backend
    handler.assert_awaited_once()
    mocked_ensure_credential.assert_called_once_with(request, circuit)


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

    frontend = PortFrontend(root_context=root_context)
    frontend.circuits = {
        unused_tcp_port: create_circuit(unused_tcp_port).model_copy(update={"open_to_public": True})
    }
    frontend.backends = {unused_tcp_port: mocker.MagicMock(proxy_http=record_request_body)}
    await frontend.start()
    yield _ServingPortFrontend(
        port=unused_tcp_port,
        bodies_received_by_backend=bodies_received_by_backend,
    )
    await frontend.stop()


async def test_proxy_passes_compressed_request_body_as_received(
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

from __future__ import annotations

from datetime import datetime
from uuid import UUID

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
from ai.backend.common.types import ModelServiceStatus, RuntimeVariant


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
            runtime_variant=RuntimeVariant.VLLM,
        ),
        subdomain=None,
        runtime_variant=RuntimeVariant.VLLM,
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
                health_status=ModelServiceStatus.HEALTHY,
                last_health_check=datetime(2024, 7, 16, 5, 45, 45, 982450).timestamp(),
                consecutive_failures=0,
            )
        ],
        session_ids=[UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452),
    )


@pytest.fixture
def port_frontend(mocker: pytest_mock.MockerFixture) -> PortFrontend:
    frontend = PortFrontend(root_context=mocker.MagicMock())
    frontend.circuits = {}
    frontend.backends = {}
    return frontend


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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

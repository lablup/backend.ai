from datetime import datetime
from typing import Any, Dict
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.agent.utils import update_nested_dict
from ai.backend.wsproxy.exceptions import GenericBadRequest
from ai.backend.wsproxy.proxy.frontend.http.port import PortFrontend
from ai.backend.wsproxy.types import AppMode, Circuit, FrontendMode, ProxyProtocol, RouteInfo


def create_circuit(**overrides) -> Circuit:
    default_values = {
        "id": UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        "app": "ttyd",
        "protocol": ProxyProtocol.HTTP,
        "worker": UUID("00000000-0000-0000-0000-000000000000"),
        "app_mode": AppMode.INTERACTIVE,
        "frontend_mode": FrontendMode.PORT,
        "envs": {},
        "arguments": None,
        "open_to_public": False,
        "allowed_client_ips": None,
        "port": 8080,
        "user_id": UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "endpoint_id": None,
        "route_info": [
            RouteInfo(
                session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=30729,
                protocol=ProxyProtocol.HTTP,
                traffic_ratio=1.0,
            )
        ],
        "session_ids": [UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        "created_at": datetime(2024, 7, 16, 5, 45, 45, 982446),
        "updated_at": datetime(2024, 7, 16, 5, 45, 45, 982452),
    }
    update_nested_dict(default_values, overrides)
    return Circuit(**default_values)  # type: ignore


class DummyRequest:
    def __init__(self, app_data: Dict[str, Any]):
        self.app = app_data
        self._state: Dict[str, Any] = {}

    def __getitem__(self, key: str):
        return self._state[key]

    def __setitem__(self, key: str, value: Any):
        self._state[key] = value


@pytest.fixture
def port_frontend(mocker):
    frontend = PortFrontend(root_context=mocker.MagicMock())
    frontend.circuits = {}
    frontend.backends = {}
    return frontend


@pytest.mark.asyncio
async def test_ensure_slot_unregistered_port(mocker, port_frontend):
    """
    Test that a GenericBadRequest is raised for an unregistered port.
    """
    port = 10200
    request = DummyRequest({"port": port})
    handler = mocker.AsyncMock()

    with pytest.raises(GenericBadRequest):
        await port_frontend._ensure_slot(request, handler)


@pytest.mark.asyncio
async def test_ensure_slot_no_circuit(mocker, port_frontend):
    """
    Test that a GenericBadRequest is raised when no circuit is available for a registered port.
    """
    port = 10200
    request = DummyRequest({"port": port})
    port_frontend.circuits[port] = None
    port_frontend.backends[port] = mocker.MagicMock()
    handler = mocker.AsyncMock()

    with pytest.raises(GenericBadRequest):
        await port_frontend._ensure_slot(request, handler)


@pytest.mark.asyncio
async def test_ensure_slot(mocker, port_frontend):
    """
    Test the normal flow where a circuit and backend are properly set up.
    """
    port = 10200
    circuit = create_circuit(port=port)
    backend = mocker.MagicMock()
    request = DummyRequest({"port": port})
    port_frontend.circuits[port] = circuit
    port_frontend.backends[port] = backend
    handler = mocker.AsyncMock(return_value=web.Response(text="success"))

    mocker.patch.object(port_frontend, "ensure_credential")

    response = await port_frontend._ensure_slot(request, handler)

    assert response.text == "success"
    assert request["circuit"] == circuit
    assert request["backend"] == backend
    handler.assert_awaited_once()
    port_frontend.ensure_credential.assert_called_once_with(request, circuit)

from typing import Any, Dict

import pytest
from aiohttp import web

from ai.backend.wsproxy.exceptions import GenericBadRequest
from ai.backend.wsproxy.proxy.frontend.http.port import PortFrontend


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
async def test_ensure_slot(mocker, port_frontend, create_circuit):
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

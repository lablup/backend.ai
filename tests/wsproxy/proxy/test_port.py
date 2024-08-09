import pytest
from aiohttp import web

from ai.backend.wsproxy.exceptions import GenericBadRequest


@pytest.mark.asyncio
async def test_ensure_slot_unregistered_port(mocker, dummy_request, port_frontend):
    """
    Test that a GenericBadRequest is raised for an unregistered port.
    """
    port = 10200
    request = dummy_request({"port": port})
    handler = mocker.AsyncMock()

    with pytest.raises(GenericBadRequest):
        await port_frontend._ensure_slot(request, handler)


@pytest.mark.asyncio
async def test_ensure_slot_no_circuit(mocker, dummy_request, port_frontend):
    """
    Test that a GenericBadRequest is raised when no circuit is available for a registered port.
    """
    port = 10200
    request = dummy_request({"port": port})
    port_frontend.circuits[port] = None
    port_frontend.backends[port] = mocker.MagicMock()
    handler = mocker.AsyncMock()

    with pytest.raises(GenericBadRequest):
        await port_frontend._ensure_slot(request, handler)


@pytest.mark.asyncio
async def test_ensure_slot(mocker, dummy_request, port_frontend, create_circuit):
    """
    Test the normal flow where a circuit and backend are properly set up.
    """
    port = 10200
    circuit = create_circuit(port)
    backend = mocker.MagicMock()
    request = dummy_request({"port": port})
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

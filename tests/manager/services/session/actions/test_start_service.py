from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_start_service_rpc(mocker):
    # Mock increment_session_usage
    mock_increment_usage = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )

    # Mock start_service agent RPC call
    mock_start_service = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.start_service",
        new_callable=AsyncMock,
    )
    mock_start_service.return_value = {"status": "success"}

    # Mock query_wsproxy_status
    mock_query_wsproxy = mocker.patch(
        "ai.backend.manager.services.session.service.query_wsproxy_status",
        new_callable=AsyncMock,
    )
    mock_query_wsproxy.return_value = {"advertise_address": "localhost:8080"}

    # Mock get_scaling_group_wsproxy_addr to return a valid address
    mock_get_wsproxy_addr = mocker.patch.object(
        mocker.MagicMock(),
        "get_scaling_group_wsproxy_addr",
        new_callable=AsyncMock,
    )
    mock_get_wsproxy_addr.return_value = "localhost:8080"

    # Mock aiohttp client session for wsproxy POST request
    mock_response = mocker.MagicMock()
    mock_response.json = AsyncMock(return_value={"token": "test_token"})

    mock_post_context = mocker.MagicMock()
    mock_post_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_context.__aexit__ = AsyncMock(return_value=None)

    mock_session_context = mocker.MagicMock()
    mock_session_context.post = mocker.MagicMock(return_value=mock_post_context)
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_context)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    mock_client_session = mocker.patch("aiohttp.ClientSession")
    mock_client_session.return_value = mock_session_context

    return {
        "increment_usage": mock_increment_usage,
        "start_service": mock_start_service,
        "query_wsproxy": mock_query_wsproxy,
        "client_session": mock_client_session,
    }


START_SERVICE_MOCK = {"started": True, "port": 8080}


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Start service",
            StartServiceAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                service="test_service",
                login_session_token="test_token",
                port=8080,
                arguments=None,
                envs=None,
            ),
            StartServiceActionResult(
                result=None,  # start_service returns None in result
                session_data=SESSION_FIXTURE_DATA,
                token="test_token",
                wsproxy_addr="localhost:8080",
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "agents": [AGENT_FIXTURE_DICT],
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [
                {
                    **KERNEL_FIXTURE_DICT,
                    "service_ports": [
                        {
                            "name": "test_service",
                            "protocol": "http",
                            "container_ports": [8080],
                            "host_ports": [18080],
                            "is_inference": False,
                        }
                    ],
                }
            ],
        }
    ],
)
async def test_start_service(
    mock_start_service_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[StartServiceAction, StartServiceActionResult],
):
    # Execute the action
    result = await processors.start_service.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, StartServiceActionResult)
    assert result.result is None  # start_service returns None in result
    assert result.token == "test_token"
    assert result.wsproxy_addr == "localhost:8080"

    # Verify session_data is properly returned
    assert result.session_data is not None
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify that agent RPC calls were made
    mock_start_service_rpc["increment_usage"].assert_called_once()
    mock_start_service_rpc["start_service"].assert_called_once()

    # Verify external dependencies were called
    mock_start_service_rpc["query_wsproxy"].assert_called_once()
    assert mock_start_service_rpc["client_session"].called  # aiohttp.ClientSession was called

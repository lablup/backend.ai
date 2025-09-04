from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)

GET_DIRECT_ACCESS_INFO_MOCK = {
    "kernel_role": "SYSTEM",
    "session_type": "SYSTEM",
    "public_host": "example.com",
    "sshd_ports": ["8023"],  # sftpd ports take precedence over sshd
}


@pytest.fixture
def mock_increment_session_usage_rpc(mocker):
    mock_increment_usage = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )
    return mock_increment_usage


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Get direct access info",
            GetDirectAccessInfoAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            GetDirectAccessInfoActionResult(
                result={},  # Empty result for non-private session type (INTERACTIVE)
                session_data=SESSION_FIXTURE_DATA,  # Expected session data
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
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_get_direct_access_info(
    mock_increment_session_usage_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[GetDirectAccessInfoAction, GetDirectAccessInfoActionResult],
    session_repository,
):
    # Execute the action
    result = await processors.get_direct_access_info.wait_for_complete(test_scenario.input)

    # Verify the result content matches expected
    assert result is not None
    assert isinstance(result, GetDirectAccessInfoActionResult)
    assert result.result == {}  # Empty result for non-private session type

    # Verify session_data is properly returned (converted from SessionRow to SessionData)
    assert result.session_data is not None
    assert isinstance(result.session_data, SessionData)
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify that agent RPC mock is available (following agent RPC call mocking pattern)
    assert mock_increment_session_usage_rpc is not None

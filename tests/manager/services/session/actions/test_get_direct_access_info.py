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

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_session_repository_methods(mocker):
    """Mock SessionRepository methods to return test data"""
    # Create a mock session with main_kernel and agent_row
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    mock_session.id = SESSION_FIXTURE_DATA.id
    mock_session.name = SESSION_FIXTURE_DATA.name
    mock_session.access_key = SESSION_FIXTURE_DATA.access_key
    # Must be a private session type for direct access
    from ai.backend.common.types import SessionTypes

    mock_session.session_type = SessionTypes.SYSTEM

    # Mock to_dataclass method to return consistent SessionData
    mock_session.to_dataclass.return_value = SESSION_FIXTURE_DATA

    # Mock main_kernel with agent_row and service_ports
    mock_kernel = MagicMock()
    mock_kernel.id = "test_kernel_id"
    mock_kernel.status = MagicMock()
    mock_kernel.status.name = "RUNNING"

    # Mock agent_row with public_host
    mock_agent = MagicMock()
    mock_agent.public_host = "example.com"
    mock_kernel.agent_row = mock_agent

    # Mock service_ports
    mock_kernel.service_ports = [
        {"name": "sshd", "host_ports": ["8022"]},
        {"name": "sftpd", "host_ports": ["8023"]},
    ]

    mock_session.main_kernel = mock_kernel

    mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_session_validated",
        new_callable=AsyncMock,
        return_value=mock_session,
    )

    return mock_session


GET_DIRECT_ACCESS_INFO_MOCK = {
    "kernel_role": "SYSTEM",
    "session_type": "SYSTEM",
    "public_host": "example.com",
    "sshd_ports": ["8023"],  # sftpd ports take precedence over sshd
}


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Get direct access info",
            GetDirectAccessInfoAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            GetDirectAccessInfoActionResult(
                result=GET_DIRECT_ACCESS_INFO_MOCK,
                session_data=SESSION_FIXTURE_DATA,  # Expected session data
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_get_direct_access_info(
    mock_session_repository_methods,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDirectAccessInfoAction, GetDirectAccessInfoActionResult],
):
    # Execute the action
    result = await processors.get_direct_access_info.wait_for_complete(test_scenario.input)

    # Verify the result content matches expected
    assert result is not None
    assert isinstance(result, GetDirectAccessInfoActionResult)
    assert result.result == GET_DIRECT_ACCESS_INFO_MOCK

    # Verify session_data is properly returned (converted from SessionRow to SessionData)
    assert result.session_data is not None
    assert isinstance(result.session_data, SessionData)
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

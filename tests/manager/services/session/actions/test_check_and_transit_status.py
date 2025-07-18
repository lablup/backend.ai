from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
    CheckAndTransitStatusActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_check_and_transit_status_rpc(mocker, mock_agent_response_result):
    # Mock the repository method for non-admin users
    mock_get_session = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_session_to_determine_status",
        new_callable=AsyncMock,
    )
    from ai.backend.manager.models.kernel import KernelRow
    from ai.backend.manager.models.session import SessionRow

    # Create a mock session
    mock_session = SessionRow(**SESSION_FIXTURE_DICT)
    mock_kernel = KernelRow(**KERNEL_FIXTURE_DICT)
    mock_session.kernels = [mock_kernel]
    mock_get_session.return_value = mock_session

    return mock_session


CHECK_AND_TRANSIT_STATUS_MOCK = {cast(SessionId, SESSION_FIXTURE_DATA.id): "RUNNING"}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Check and transit status",
                CheckAndTransitStatusAction(
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_role=UserRole.USER,
                    session_id=cast(SessionId, SESSION_FIXTURE_DATA.id),
                ),
                CheckAndTransitStatusActionResult(
                    result=CHECK_AND_TRANSIT_STATUS_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            CHECK_AND_TRANSIT_STATUS_MOCK,
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
async def test_check_and_transit_status(
    mock_check_and_transit_status_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[CheckAndTransitStatusAction, CheckAndTransitStatusActionResult],
):
    # Execute the actual service
    result = await processors.check_and_transit_status.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, CheckAndTransitStatusActionResult)
    assert result.session_data is not None
    assert result.result is not None

    # The actual service returns empty dict for non-admin users accessing their own session
    expected_session_data = mock_check_and_transit_status_rpc.to_dataclass()
    assert result.session_data.id == expected_session_data.id

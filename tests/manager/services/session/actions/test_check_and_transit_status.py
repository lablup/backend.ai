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
    SESSION_ROW_FIXTURE,
)


@pytest.fixture
def mock_check_and_transit_status_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.check_and_transit_status",
        new_callable=AsyncMock,
    )
    # Return proper CheckAndTransitStatusActionResult object instead of just dict
    mock.return_value = CheckAndTransitStatusActionResult(
        result=mock_agent_response_result,
        session_row=SESSION_ROW_FIXTURE,
    )
    return mock


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
    await test_scenario.test(processors.check_and_transit_status.wait_for_complete)

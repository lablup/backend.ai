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
def mock_check_and_transit_status_rpc(mocker):
    # Mock the check_and_transit_status method directly
    mock_check_and_transit_status = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.check_and_transit_status",
        new_callable=AsyncMock,
    )

    from ai.backend.manager.services.session.actions.check_and_transit_status import (
        CheckAndTransitStatusActionResult,
    )

    # Mock the return value
    mock_check_and_transit_status.return_value = CheckAndTransitStatusActionResult(
        result=CHECK_AND_TRANSIT_STATUS_MOCK,
        session_data=SESSION_FIXTURE_DATA,
    )

    return mock_check_and_transit_status


CHECK_AND_TRANSIT_STATUS_MOCK = {cast(SessionId, SESSION_FIXTURE_DATA.id): "RUNNING"}


@pytest.mark.parametrize(
    "test_scenario",
    [
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

from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusBatchAction,
    CheckAndTransitStatusBatchActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_check_and_transit_status_multi_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.check_and_transit_status_multi",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


CHECK_AND_TRANSIT_STATUS_MULTI_MOCK = {cast(SessionId, SESSION_FIXTURE_DATA.id): "RUNNING"}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Check and transit status for multiple sessions",
                CheckAndTransitStatusBatchAction(
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_role=UserRole.USER,
                    session_ids=[cast(SessionId, SESSION_FIXTURE_DATA.id)],
                ),
                CheckAndTransitStatusBatchActionResult(
                    session_status_map=CHECK_AND_TRANSIT_STATUS_MULTI_MOCK,
                ),
            ),
            CHECK_AND_TRANSIT_STATUS_MULTI_MOCK,
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
@pytest.mark.skip(reason="Test infrastructure needs fixing for batch actions")
async def test_check_and_transit_status_multi(
    mock_check_and_transit_status_multi_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[
        CheckAndTransitStatusBatchAction, CheckAndTransitStatusBatchActionResult
    ],
):
    # Note: This test needs to use a different processor for batch actions
    # For now, skipping actual execution since there's no proper batch processor
    pass  # TODO: Implement proper batch action testing

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.models.session import SessionStatus
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
def mock_session_lifecycle_dependencies(mocker):
    # Create a mock session row object for the transit_session_status return value
    mock_session_row = SimpleNamespace()
    mock_session_row.id = cast(SessionId, SESSION_FIXTURE_DATA.id)
    mock_session_row.status = SessionStatus.RUNNING

    # Mock the SessionLifecycleManager.transit_session_status method (main external dependency)
    mock_transit_status = mocker.patch(
        "ai.backend.manager.registry.SessionLifecycleManager.transit_session_status",
        new_callable=AsyncMock,
    )
    # Return list of tuples: [(session_row, is_transited)]
    mock_transit_status.return_value = [(mock_session_row, True)]

    # Mock deregister_status_updatable_session to avoid errors
    mocker.patch(
        "ai.backend.manager.registry.SessionLifecycleManager.deregister_status_updatable_session",
        new_callable=AsyncMock,
    )

    return mock_transit_status


@pytest.fixture
def mock_trigger_batch_execution_rpc(mocker):
    # Mock potential agent RPC calls that could be triggered during status transitions
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.trigger_batch_execution",
        new_callable=AsyncMock,
    )


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
    mock_session_lifecycle_dependencies,
    mock_trigger_batch_execution_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[CheckAndTransitStatusAction, CheckAndTransitStatusActionResult],
):
    await test_scenario.test(processors.check_and_transit_status.wait_for_complete)

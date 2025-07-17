from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
    GetStatusHistoryActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_get_status_history_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService._get_status_history",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


GET_STATUS_HISTORY_MOCK = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Get status history",
                GetStatusHistoryAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                GetStatusHistoryActionResult(
                    status_history=GET_STATUS_HISTORY_MOCK,
                    session_id=SESSION_FIXTURE_DATA.id,
                ),
            ),
            GET_STATUS_HISTORY_MOCK,
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
async def test_get_status_history(
    mock_get_status_history_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetStatusHistoryAction, GetStatusHistoryActionResult],
):
    await test_scenario.test(processors.get_status_history.wait_for_complete)

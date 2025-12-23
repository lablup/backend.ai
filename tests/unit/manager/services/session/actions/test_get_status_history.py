from typing import cast

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
    GetStatusHistoryActionResult,
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

GET_STATUS_HISTORY_MOCK = {
    "history": [
        {"status": "PENDING", "timestamp": "2023-01-01T00:00:00Z"},
        {"status": "RUNNING", "timestamp": "2023-01-01T00:01:00Z"},
    ]
}


@pytest.fixture
def mock_get_status_history_rpc(mocker):
    """Mock the get_status_history service method"""
    from ai.backend.manager.services.session.service import SessionService

    mock_method = mocker.patch.object(
        SessionService,
        "get_status_history",
        new_callable=mocker.AsyncMock,
    )

    from ai.backend.manager.services.session.actions.get_status_history import (
        GetStatusHistoryActionResult,
    )

    mock_method.return_value = GetStatusHistoryActionResult(
        status_history=GET_STATUS_HISTORY_MOCK,
        session_id=SESSION_FIXTURE_DATA.id,
    )

    return mock_method


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
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
async def test_get_status_history(
    mock_get_status_history_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[GetStatusHistoryAction, GetStatusHistoryActionResult],
    session_repository,
):
    await test_scenario.test(processors.get_status_history.wait_for_complete)

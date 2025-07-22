from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
    ExecuteSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)


@pytest.fixture
def mock_agent_execute_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.execute",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


@pytest.fixture
def mock_increment_session_usage_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )
    return mock


EXECUTE_SESSION_RAW_RESULT = {
    "status": "finished",
    "runId": "test_run_123",
    "exitCode": 0,
    "options": {},
    "files": [],
    "stdout": None,
    "stderr": None,
    "media": None,
    "html": None,
}
EXECUTE_SESSION_MOCK = {"result": EXECUTE_SESSION_RAW_RESULT}

EXECUTE_SESSION_ERROR_RESULT = {
    "status": "finished",
    "runId": "test_run_error",
    "exitCode": 1,
    "options": {},
    "files": [],
    "stdout": None,
    "stderr": "ZeroDivisionError: division by zero",
    "media": None,
    "html": None,
}
EXECUTE_SESSION_ERROR_MOCK = {"result": EXECUTE_SESSION_ERROR_RESULT}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Execute session",
                ExecuteSessionAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    api_version=(1, 0),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    params=ExecuteSessionActionParams(
                        mode="query",
                        options=None,
                        code="print('Hello World')",
                        run_id="test_run_123",
                    ),
                ),
                ExecuteSessionActionResult(
                    result=EXECUTE_SESSION_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            EXECUTE_SESSION_RAW_RESULT,
        ),
        (
            TestScenario.success(
                "Execute session with error",
                ExecuteSessionAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    api_version=(1, 0),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    params=ExecuteSessionActionParams(
                        mode="query",
                        options=None,
                        code="1 / 0",  # Division by zero
                        run_id="test_run_error",
                    ),
                ),
                ExecuteSessionActionResult(
                    result=EXECUTE_SESSION_ERROR_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            EXECUTE_SESSION_ERROR_RESULT,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_execute_session(
    mock_agent_execute_rpc,
    mock_increment_session_usage_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[ExecuteSessionAction, ExecuteSessionActionResult],
    session_repository,
):
    await test_scenario.test(processors.execute_session.wait_for_complete)
